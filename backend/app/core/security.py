"""Băm mật khẩu và phát hành / kiểm tra JWT."""

import base64
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]


def _prehash(password: str) -> bytes:
    """Rút mật khẩu về 44 byte cố định trước khi đưa vào bcrypt.

    bcrypt chỉ dùng 72 byte đầu và ném lỗi nếu dài hơn. Mật khẩu tiếng Việt có
    dấu tốn 3 byte mỗi ký tự nên chỉ ~24 ký tự đã chạm trần. SHA-256 rồi
    base64 cho ra độ dài cố định, không cắt cụt và không giới hạn ký tự.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(password), password_hash.encode("ascii"))
    except ValueError:
        # Hash trong DB hỏng/sai định dạng: coi như sai mật khẩu, không để
        # exception lọt ra thành lỗi 500 làm lộ thông tin nội bộ.
        return False


def _create_token(subject: str, token_type: TokenType, expires_in: timedelta, **extra: Any) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_in,
        **extra,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    return _create_token(
        subject=str(user_id),
        token_type="access",
        expires_in=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        role=role,
    )


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    """Trả về (token, jti, thời điểm hết hạn).

    jti được lưu xuống DB để logout thu hồi được token — nếu chỉ xoá cookie
    thì token bị đánh cắp vẫn dùng được tới khi hết hạn.
    """
    jti = str(uuid.uuid4())
    expires_in = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = _create_token(
        subject=str(user_id), token_type="refresh", expires_in=expires_in, jti=jti
    )
    return token, jti, datetime.now(UTC) + expires_in


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any] | None:
    """Trả về payload nếu token hợp lệ, None nếu hỏng/hết hạn/sai loại.

    Kiểm tra `type` để access token không dùng thay refresh token được và
    ngược lại.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None

    if payload.get("type") != expected_type:
        return None
    return payload
