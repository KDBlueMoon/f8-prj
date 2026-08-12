"""Tra cứu mã số thuế qua VietQR và khâu đối chiếu tên công ty lúc đăng ký."""

from collections.abc import Callable

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.company import Company
from tests.conftest import PASSWORD, VIETQR_ROUTE

LOOKUP = "/api/v1/companies/lookup-tax-code"
REGISTER_EMPLOYER = "/api/v1/auth/register/employer"

REAL_NAME = "CÔNG TY TNHH CASSO"


def vietqr_success(name: str = REAL_NAME) -> httpx.Response:
    """Phản hồi thật của VietQR — chỉ có 4 trường này, không có director/phone."""
    return httpx.Response(
        200,
        json={
            "code": "00",
            "desc": "Success - Thành công",
            "data": {
                "id": "0316794479",
                "name": name,
                "internationalName": "CASSO COMPANY LIMITED",
                "shortName": "CASSO",
                "address": "Số 1 Đường Test, Quận 1, TP.HCM",
            },
        },
    )


def vietqr_not_found() -> httpx.Response:
    return httpx.Response(200, json={"code": "51", "desc": "Không tìm thấy", "data": None})


# ─────────────────────────── Endpoint tra cứu ───────────────────────────


def test_lookup_returns_the_four_fields_vietqr_provides(
    client: TestClient, vietqr_mock: respx.MockRouter
) -> None:
    vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_success())

    response = client.get(f"{LOOKUP}/0316794479")

    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == REAL_NAME
    assert body["international_name"] == "CASSO COMPANY LIMITED"
    assert body["short_name"] == "CASSO"
    assert body["headquarters_address"]
    # VietQR không trả người đại diện và số điện thoại — không được bịa ra.
    assert "director" not in body
    assert "phone_number" not in body


def test_lookup_returns_404_when_tax_code_not_registered(
    client: TestClient, vietqr_mock: respx.MockRouter
) -> None:
    vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_not_found())

    response = client.get(f"{LOOKUP}/0316794479")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "TAX_CODE_NOT_FOUND"


@pytest.mark.parametrize(
    "side_effect",
    [httpx.ConnectTimeout("timeout"), httpx.ConnectError("mat mang")],
    ids=["timeout", "mat-ket-noi"],
)
def test_lookup_returns_503_when_vietqr_unreachable(
    client: TestClient, vietqr_mock: respx.MockRouter, side_effect: Exception
) -> None:
    vietqr_mock[VIETQR_ROUTE].mock(side_effect=side_effect)

    response = client.get(f"{LOOKUP}/0316794479")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "TAX_LOOKUP_UNAVAILABLE"


@pytest.mark.parametrize("upstream_status", [429, 500, 502, 503])
def test_lookup_maps_upstream_failures_to_unavailable(
    client: TestClient, vietqr_mock: respx.MockRouter, upstream_status: int
) -> None:
    """VietQR bị quá tải hoặc lỗi phải thành 503 của mình, không lộ mã lỗi gốc."""
    vietqr_mock[VIETQR_ROUTE].mock(return_value=httpx.Response(upstream_status))

    response = client.get(f"{LOOKUP}/0316794479")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "TAX_LOOKUP_UNAVAILABLE"


@pytest.mark.parametrize("tax_code", ["123456789", "abcdefghij", "12345678901"])
def test_lookup_rejects_malformed_tax_code(client: TestClient, tax_code: str) -> None:
    response = client.get(f"{LOOKUP}/{tax_code}")

    assert response.status_code in (400, 422)


def test_lookup_caches_result_to_avoid_repeat_calls(
    client: TestClient, vietqr_mock: respx.MockRouter
) -> None:
    """Gọi lại cùng mã số thuế không được đụng VietQR lần nữa (tránh dính 429)."""
    route = vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_success())

    client.get(f"{LOOKUP}/0316794479")
    client.get(f"{LOOKUP}/0316794479")
    client.get(f"{LOOKUP}/0316794479")

    assert route.call_count == 1


def test_lookup_caches_not_found_results_too(
    client: TestClient, vietqr_mock: respx.MockRouter
) -> None:
    """Kết quả "không tìm thấy" cũng phải cache.

    Đo thực tế: VietQR trả lời tìm thấy trong ~0,2 giây nhưng mất ~5,3 giây mới
    trả lời không tìm thấy. Hỏi lại mỗi lần là bắt người dùng chờ vô ích.
    """
    route = vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_not_found())

    first = client.get(f"{LOOKUP}/0316794479")
    second = client.get(f"{LOOKUP}/0316794479")

    assert first.status_code == second.status_code == 404
    assert second.json()["detail"]["code"] == "TAX_CODE_NOT_FOUND"
    assert route.call_count == 1


def test_lookup_is_rate_limited(client: TestClient, vietqr_mock: respx.MockRouter) -> None:
    """Chặn dùng endpoint công khai này để quét dữ liệu doanh nghiệp hàng loạt."""
    vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_success())

    # Mã số thuế khác nhau để không ăn cache.
    statuses = [client.get(f"{LOOKUP}/031679{i:04d}").status_code for i in range(12)]

    assert 429 in statuses


# ────────────────── Đối chiếu tên công ty lúc đăng ký ──────────────────


def _employer_payload(email: str, tax_code: str, company_name: str) -> dict:
    return {
        "email": email,
        "password": PASSWORD,
        "full_name": "Người Đăng Ký",
        "company": {
            "tax_code": tax_code,
            "company_name": company_name,
            "director": "Nguyễn Văn A",
            "headquarters_address": "1 Đường Test, Hà Nội",
            "email": "hr@test.vn",
            "phone_number": "0901234567",
            "company_size": "10-24",
        },
    }


def test_registration_blocked_when_company_name_does_not_match_tax_code(
    client: TestClient,
    vietqr_mock: respx.MockRouter,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
) -> None:
    """Chặn sửa payload để khai tên công ty khác với mã số thuế."""
    vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_success(REAL_NAME))

    response = client.post(
        REGISTER_EMPLOYER,
        json=_employer_payload(unique_email(), unique_tax_code(), "CÔNG TY MẠO DANH"),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "TAX_CODE_NAME_MISMATCH"
    # Báo tên đúng để người dùng biết cần sửa thành gì.
    assert REAL_NAME in response.json()["detail"]["message"]


@pytest.mark.parametrize(
    "typed_name",
    ["CÔNG TY TNHH CASSO", "  công ty tnhh casso  ", "CÔNG TY   TNHH   CASSO"],
    ids=["giong-het", "khac-hoa-thuong-va-khoang-trang", "thua-khoang-trang-giua"],
)
def test_registration_accepts_name_differing_only_in_case_or_spacing(
    client: TestClient,
    db: Session,
    vietqr_mock: respx.MockRouter,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
    typed_name: str,
) -> None:
    vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_success(REAL_NAME))
    email = unique_email()
    cleanup_users.append(email)

    response = client.post(
        REGISTER_EMPLOYER, json=_employer_payload(email, unique_tax_code(), typed_name)
    )

    assert response.status_code == 201
    company = db.scalar(select(Company).where(Company.id == response.json()["company"]["id"]))
    assert company is not None
    assert company.tax_code_verified_at is not None


def test_registration_proceeds_when_vietqr_is_down_but_marks_unverified(
    client: TestClient,
    db: Session,
    vietqr_mock: respx.MockRouter,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
) -> None:
    """VietQR chết KHÔNG được chặn người dùng đăng ký.

    Đổi lại, hồ sơ không có dấu đối chiếu để admin biết mà soi kỹ khi duyệt.
    """
    vietqr_mock[VIETQR_ROUTE].mock(side_effect=httpx.ConnectTimeout("VietQR chet"))
    email = unique_email()
    cleanup_users.append(email)

    response = client.post(
        REGISTER_EMPLOYER, json=_employer_payload(email, unique_tax_code(), "CÔNG TY BẤT KỲ")
    )

    assert response.status_code == 201
    company = db.scalar(select(Company).where(Company.id == response.json()["company"]["id"]))
    assert company is not None
    assert company.tax_code_verified_at is None


def test_registration_blocked_when_tax_code_does_not_exist(
    client: TestClient,
    vietqr_mock: respx.MockRouter,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
) -> None:
    vietqr_mock[VIETQR_ROUTE].mock(return_value=vietqr_not_found())

    response = client.post(
        REGISTER_EMPLOYER,
        json=_employer_payload(unique_email(), unique_tax_code(), "CÔNG TY KHÔNG CÓ THẬT"),
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "TAX_CODE_NOT_FOUND"
