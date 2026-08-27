"""Băm mật khẩu và phát hành / kiểm tra JWT (access token duy nhất, không refresh)."""

import base64
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from config.settings import settings


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
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Trả về payload nếu chữ ký hợp lệ và chưa hết hạn, None nếu không.

    Verify signature đầy đủ bằng SECRET_KEY — khác với việc chỉ base64-decode
    phần payload mà không kiểm tra chữ ký (không an toàn, ai cũng giả mạo
    token được).
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
