import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.db.models.enums import CompanySize, CompanyStatus, UserRole, VerificationTier
from app.schemas.validators import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    validate_optional_phone,
    validate_password,
    validate_required_phone,
    validate_tax_code,
)


class RegisterCandidateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    full_name: str = Field(min_length=2, max_length=255)
    phone_number: str | None = Field(default=None, max_length=20)

    _check_password = field_validator("password")(validate_password)
    _check_phone = field_validator("phone_number")(validate_optional_phone)


class CompanyRegistrationInfo(BaseModel):
    """Thông tin doanh nghiệp nhập lúc đăng ký tài khoản nhà tuyển dụng.

    4 trường đầu có thể tự điền bằng nút tra cứu VietQR; phần còn lại (người
    đại diện, liên hệ, quy mô, lĩnh vực) VietQR không có nên phải nhập tay.
    """

    tax_code: str = Field(max_length=14)
    company_name: str = Field(min_length=2, max_length=500)
    international_name: str | None = Field(default=None, max_length=500)
    short_name: str | None = Field(default=None, max_length=255)
    director: str = Field(min_length=2, max_length=255)
    headquarters_address: str = Field(min_length=5)
    email: EmailStr
    phone_number: str = Field(max_length=20)
    company_size: CompanySize
    website: str | None = Field(default=None, max_length=500)
    issued_date: date | None = None
    category_group_id: uuid.UUID | None = None

    _check_tax_code = field_validator("tax_code")(validate_tax_code)
    _check_phone = field_validator("phone_number")(validate_required_phone)


class RegisterEmployerRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    full_name: str = Field(min_length=2, max_length=255)
    phone_number: str | None = Field(default=None, max_length=20)
    company: CompanyRegistrationInfo

    _check_password = field_validator("password")(validate_password)
    _check_phone = field_validator("phone_number")(validate_optional_phone)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class CompanyBriefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    short_name: str | None
    slug: str
    logo_url: str | None
    status: CompanyStatus
    verification_tier: VerificationTier
    rejected_reason: str | None


class UserOut(BaseModel):
    """Thông tin người dùng trả ra API — không bao giờ chứa password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: UserRole
    full_name: str
    phone_number: str | None
    avatar_url: str | None


class MeOut(BaseModel):
    user: UserOut
    # Chỉ có giá trị với tài khoản nhà tuyển dụng.
    company: CompanyBriefOut | None = None


class LoginResponse(BaseModel):
    """Refresh token KHÔNG nằm ở đây — nó đi trong httpOnly cookie."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
    company: CompanyBriefOut | None = None
