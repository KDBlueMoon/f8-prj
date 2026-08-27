import uuid
from datetime import date

from pydantic import BaseModel, EmailStr, Field

from models.enums import CompanyStatus, VerificationTier
from schemas.auth import MIN_PASSWORD_LENGTH
from schemas.common import Address


class CompanyRegisterRequest(BaseModel):
    tax_code: str
    company_name: str
    international_name: str | None = None
    short_name: str | None = None
    director: str | None = None
    headquarters_address: str | None = None
    email: EmailStr
    phone_number: str
    website: str | None = None
    # Không có trong openapi.yaml gốc — bổ sung để công ty đăng ký xong có thể
    # đăng nhập được bằng /auth/login (spec gốc không có field này).
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)


class CompanyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    status: CompanyStatus
    verification_tier: VerificationTier
    tax_code: str
    company_name: str
    international_name: str | None
    short_name: str | None
    director: str | None
    headquarters_address: str | None
    issued_date: date | None
    email: str
    phone_number: str
    website: str | None
    logo_url: str | None
    company_size: str | None
    category: str | None
    # Không có endpoint nào ghi địa chỉ chi nhánh (CompanyRegisterRequest
    # không có field này) nên luôn rỗng — giữ field để khớp schema Company.
    address_list: list[Address] = Field(default_factory=list)
    description_html: str | None
