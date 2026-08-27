"""Xác thực JWT + dọn session sau mỗi request.

`SessionCleanupMiddleware` đảm bảo `session.remove()` luôn chạy dù request lỗi
ở ngay bước xác thực (trước khi vào tới router, nên decorator `@transaction`
trong `utils/db.py` chưa kịp chạy `finally` của chính nó) — tránh session của
`scoped_session` bị giữ lại sang request sau dùng chung thread.

`get_current_user` / `require_role` verify chữ ký JWT bằng `pyjwt` (không chỉ
base64-decode phần payload) rồi tra `User` tương ứng — đây là chốt chặn quyền
thật của hệ thống, không phải việc của client.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config.database import session
from models.enums import UserRole
from models.user import User
from utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


class SessionCleanupMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        try:
            return await call_next(request)
        finally:
            session.remove()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa đăng nhập")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token không hợp lệ hoặc đã hết hạn")

    user = User.get_by_id(uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không tồn tại")
    return user


def require_role(*roles: UserRole):  # type: ignore[no-untyped-def]
    def _dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền truy cập")
        return user

    return _dependency
