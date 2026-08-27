import uuid

from pydantic import BaseModel, EmailStr, Field

from models.enums import UserRole

MIN_PASSWORD_LENGTH = 8


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Đăng ký tài khoản Candidate — không có trong openapi.yaml gốc, bổ sung
    vì flow apply job cần một cách để tạo tài khoản Candidate."""

    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    full_name: str


class AuthUser(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    role: UserRole


class AuthResponse(BaseModel):
    access_token: str
    user: AuthUser
