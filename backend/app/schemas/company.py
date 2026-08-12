import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.db.models.enums import CompanySize, CompanyStatus, UserRole, VerificationTier
from app.schemas.validators import validate_optional_phone

MAX_REJECTED_REASON_LENGTH = 1000


class TaxCodeLookupOut(BaseModel):
    """Kết quả tra cứu VietQR.

    Chỉ có 4 trường này được tự điền. Người đại diện, số điện thoại, email,
    ngày cấp, quy mô và lĩnh vực VietQR không trả về — nhà tuyển dụng nhập tay.
    """

    tax_code: str
    company_name: str
    international_name: str | None
    short_name: str | None
    headquarters_address: str | None


class CompanyAddressIn(BaseModel):
    city_id: int
    address_detail: str = Field(min_length=3, max_length=500)


class CompanyAddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    city_id: int
    address_detail: str


class CompanyOut(BaseModel):
    """Hồ sơ công ty đầy đủ, dùng cho nhà tuyển dụng xem của mình và cho admin."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tax_code: str
    company_name: str
    international_name: str | None
    short_name: str | None
    slug: str
    director: str
    headquarters_address: str
    issued_date: date | None
    email: EmailStr
    phone_number: str
    website: str | None
    logo_url: str | None
    company_size: CompanySize
    category_group_id: uuid.UUID | None
    description_html: str | None
    status: CompanyStatus
    rejected_reason: str | None
    verification_tier: VerificationTier
    tax_code_verified_at: datetime | None
    created_at: datetime
    addresses: list[CompanyAddressOut]


class CompanyUpdateIn(BaseModel):
    """Các trường nhà tuyển dụng được tự sửa.

    Cố ý KHÔNG cho sửa `tax_code`: mã số thuế là khoá nghiệp vụ đã dùng để đối
    chiếu VietQR, đổi được thì có thể qua mặt khâu duyệt bằng cách đăng ký một
    mã hợp lệ rồi thay bằng mã khác.
    """

    company_name: str | None = Field(default=None, min_length=2, max_length=500)
    international_name: str | None = Field(default=None, max_length=500)
    short_name: str | None = Field(default=None, max_length=255)
    director: str | None = Field(default=None, min_length=2, max_length=255)
    headquarters_address: str | None = Field(default=None, min_length=5)
    issued_date: date | None = None
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    company_size: CompanySize | None = None
    category_group_id: uuid.UUID | None = None
    description_html: str | None = None

    _check_phone = field_validator("phone_number")(validate_optional_phone)


class CompanyListItemOut(BaseModel):
    """Bản rút gọn cho màn hình danh sách của admin."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tax_code: str
    company_name: str
    short_name: str | None
    slug: str
    director: str
    email: EmailStr
    phone_number: str
    company_size: CompanySize
    status: CompanyStatus
    verification_tier: VerificationTier
    tax_code_verified_at: datetime | None
    created_at: datetime


class AdminCompanyDecisionIn(BaseModel):
    status: CompanyStatus
    rejected_reason: str | None = Field(default=None, max_length=MAX_REJECTED_REASON_LENGTH)

    @field_validator("status")
    @classmethod
    def only_final_decisions(cls, value: CompanyStatus) -> CompanyStatus:
        """Admin chỉ duyệt hoặc từ chối; không đưa hồ sơ ngược về PENDING."""
        if value == CompanyStatus.PENDING:
            raise ValueError("Chỉ được chuyển sang APPROVED hoặc REJECTED.")
        return value


class AdminVerificationIn(BaseModel):
    verification_tier: VerificationTier


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: UserRole
    full_name: str
    phone_number: str | None
    is_active: bool
    created_at: datetime


class AdminUserStatusIn(BaseModel):
    is_active: bool
