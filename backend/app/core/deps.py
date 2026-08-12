"""Dependency dùng chung cho xác thực và phân quyền.

Đây là chốt chặn thật của hệ thống. Frontend ẩn menu chỉ để trải nghiệm đỡ rối,
không phải biện pháp bảo mật.
"""

import uuid
from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session
from starlette import status

from app.core.errors import AppError
from app.core.security import decode_token
from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db

_BEARER_PREFIX = "Bearer "


def _unauthorized() -> AppError:
    return AppError(
        "NOT_AUTHENTICATED",
        "Vui lòng đăng nhập để tiếp tục.",
        status.HTTP_401_UNAUTHORIZED,
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith(_BEARER_PREFIX):
        raise _unauthorized()

    payload = decode_token(authorization[len(_BEARER_PREFIX) :], expected_type="access")
    if payload is None:
        raise _unauthorized()

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _unauthorized() from None

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()

    # Kiểm tra lại trong DB thay vì tin vào token: admin khoá tài khoản là chặn
    # được ngay, không phải chờ access token hết hạn.
    if not user.is_active:
        raise AppError(
            "ACCOUNT_DISABLED",
            "Tài khoản đã bị khoá. Vui lòng liên hệ quản trị viên.",
            status.HTTP_403_FORBIDDEN,
        )
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Dùng cho endpoint công khai muốn cá nhân hoá khi người dùng đã đăng nhập.

    Chưa đăng nhập thì trả None chứ không báo lỗi.
    """
    try:
        return get_current_user(request, db)
    except AppError:
        return None


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Sinh dependency chỉ cho các vai trò được liệt kê đi qua."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise AppError(
                "FORBIDDEN_ROLE",
                "Tài khoản của bạn không có quyền thực hiện thao tác này.",
                status.HTTP_403_FORBIDDEN,
            )
        return user

    return dependency


require_candidate = require_role(UserRole.CANDIDATE)
require_employer = require_role(UserRole.EMPLOYER)
require_admin = require_role(UserRole.ADMIN)
