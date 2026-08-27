from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from middlewares.auth import get_current_user
from models.enums import UserRole
from models.user import User
from schemas.auth import AuthResponse, AuthUser, LoginRequest, RegisterRequest
from utils.db import transaction
from utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@transaction
def register(payload: RegisterRequest) -> AuthResponse:
    if User.get_list(email=payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")

    user = User.create(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.CANDIDATE,
        full_name=payload.full_name,
    )
    token = create_access_token(user.id, user.role.value)
    return AuthResponse(access_token=token, user=AuthUser.model_validate(user))


@router.post("/login", response_model=AuthResponse)
@transaction
def login(payload: LoginRequest) -> AuthResponse:
    matches = User.get_list(email=payload.email)
    user = matches[0] if matches else None
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai thông tin đăng nhập")

    token = create_access_token(user.id, user.role.value)
    return AuthResponse(access_token=token, user=AuthUser.model_validate(user))


@router.post("/logout")
def logout(_user: User = Depends(get_current_user)) -> dict:
    # JWT stateless, không có refresh-token/cookie để thu hồi — hết hạn tự nhiên.
    return {"message": "Đăng xuất thành công"}
