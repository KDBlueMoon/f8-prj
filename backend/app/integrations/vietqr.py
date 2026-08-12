"""Tra cứu thông tin doanh nghiệp theo mã số thuế qua VietQR.

VietQR chỉ trả 4 trường dùng được: name, internationalName, shortName, address.
KHÔNG có người đại diện và số điện thoại — hai trường này nhà tuyển dụng phải
tự nhập, dù tài liệu yêu cầu ban đầu có nhắc tới.

Gọi từ backend chứ không gọi thẳng từ trình duyệt: để kiểm soát được hạn mức,
cache lại kết quả, và không phơi chi tiết tích hợp ra client.
"""

import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
from starlette import status

from app.core.config import settings
from app.core.errors import AppError, NotFoundError

_CACHE_TTL = timedelta(hours=24)
# Cache kết quả "không tìm thấy" ngắn hơn vì doanh nghiệp mới đăng ký sẽ xuất
# hiện sau đó. Vẫn phải cache: đo thực tế cho thấy VietQR mất ~5,3 giây mới trả
# lời không tìm thấy, hỏi lại nhiều lần là bắt người dùng chờ vô ích.
_NOT_FOUND_CACHE_TTL = timedelta(minutes=30)
_SUCCESS_CODE = "00"
_WHITESPACE = re.compile(r"\s+")

# Đánh dấu mã số thuế đã tra và không tồn tại.
_NOT_FOUND = object()


@dataclass(frozen=True)
class TaxCodeInfo:
    tax_code: str
    company_name: str
    international_name: str | None
    short_name: str | None
    headquarters_address: str | None


# Cache trong bộ nhớ tiến trình: đủ để tránh gọi lại VietQR cho cùng một mã số
# thuế trong ngày và giảm nguy cơ bị 429. Chạy nhiều worker thì mỗi tiến trình
# giữ cache riêng — chấp nhận được vì dữ liệu này gần như không đổi.
_cache: dict[str, tuple[TaxCodeInfo | object, datetime]] = {}
_cache_lock = threading.Lock()

_client = httpx.Client(timeout=settings.VIETQR_TIMEOUT_SECONDS)


def clear_cache() -> None:
    """Dùng trong test để mỗi test bắt đầu với cache rỗng."""
    with _cache_lock:
        _cache.clear()


def _get_cached(tax_code: str) -> TaxCodeInfo | object | None:
    with _cache_lock:
        entry = _cache.get(tax_code)
        if entry is None:
            return None

        value, cached_at = entry
        ttl = _NOT_FOUND_CACHE_TTL if value is _NOT_FOUND else _CACHE_TTL
        if datetime.now(UTC) - cached_at > ttl:
            del _cache[tax_code]
            return None
        return value


def _put_cache(tax_code: str, value: TaxCodeInfo | object) -> None:
    with _cache_lock:
        _cache[tax_code] = (value, datetime.now(UTC))


def _not_found() -> NotFoundError:
    return NotFoundError(
        "TAX_CODE_NOT_FOUND",
        "Không tìm thấy doanh nghiệp với mã số thuế này.",
    )


def _unavailable() -> AppError:
    return AppError(
        "TAX_LOOKUP_UNAVAILABLE",
        "Không tra cứu được mã số thuế lúc này. Vui lòng nhập thông tin thủ công.",
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def lookup_tax_code(tax_code: str) -> TaxCodeInfo:
    """Tra cứu doanh nghiệp theo mã số thuế.

    Ném NotFoundError khi không tìm thấy, AppError 503 khi VietQR không phản hồi.
    Bên gọi phải xử lý được 503 mà không chặn người dùng đăng ký.
    """
    cached = _get_cached(tax_code)
    if cached is _NOT_FOUND:
        raise _not_found()
    if isinstance(cached, TaxCodeInfo):
        return cached

    try:
        response = _client.get(f"{settings.VIETQR_BASE_URL}/business/{tax_code}")
    except httpx.HTTPError:
        # Timeout, DNS hỏng, mất mạng — không phân biệt, đều là "tạm thời không dùng được".
        raise _unavailable() from None

    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        raise _unavailable()
    if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        raise _unavailable()

    try:
        body = response.json()
    except ValueError:
        raise _unavailable() from None

    if body.get("code") != _SUCCESS_CODE or not isinstance(body.get("data"), dict):
        _put_cache(tax_code, _NOT_FOUND)
        raise _not_found()

    data = body["data"]
    info = TaxCodeInfo(
        tax_code=tax_code,
        company_name=(data.get("name") or "").strip(),
        international_name=(data.get("internationalName") or "").strip() or None,
        short_name=(data.get("shortName") or "").strip() or None,
        headquarters_address=(data.get("address") or "").strip() or None,
    )

    if not info.company_name:
        # Có bản ghi nhưng thiếu tên công ty thì coi như không tra được, để
        # người dùng nhập tay thay vì lưu một công ty không có tên.
        _put_cache(tax_code, _NOT_FOUND)
        raise _not_found()

    _put_cache(tax_code, info)
    return info


def normalize_company_name(name: str) -> str:
    """Chuẩn hoá tên công ty để so khớp.

    Bỏ khác biệt về hoa/thường và khoảng trắng thừa — người dùng gõ lại tên có
    thêm dấu cách hay viết thường thì vẫn coi là khớp.
    """
    return _WHITESPACE.sub(" ", name).strip().upper()
