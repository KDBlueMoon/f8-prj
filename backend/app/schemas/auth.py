import re
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.db.models.enums import CompanySize, CompanyStatus, UserRole, VerificationTier

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

_PHONE_PATTERN = re.compile(r"^0\d{9,10}$")
_TAX_CODE_PATTERN = re.compile(r"^\d{10}(-\d{3})?$|^\d{13}$")


def _validate_password(value: str) -> str:
    """Yêu cầu tối thiểu: đủ dài, có cả chữ và số.

    Cố tình không bắt ký tự đặc biệt — quy tắc càng rườm rà người dùng càng
    hay đặt mật khẩu dễ đoán kiểu "Abc@1234".
    """
    # Đếm độ dài sau khi bỏ khoảng trắng hai đầu: "       1a" đủ 8 ký tự theo
    # min_length nhưng thực chất chỉ có 2 ký tự có nghĩa. Không tự cắt khoảng
    # trắng vì như vậy là âm thầm đổi mật khẩu người dùng đã nhập.
    if len(value.strip()) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Mật khẩu phải có tối thiểu {MIN_PASSWORD_LENGTH} ký tự, "
            "không tính khoảng trắng ở đầu và cuối."
        )
    if not any(char.isalpha() for char in value):
        raise ValueError("Mật khẩu phải có ít nhất một chữ cái.")
    if not any(char.isdigit() for char in value):
        raise ValueError("Mật khẩu phải có ít nhất một chữ số.")
    return value


class RegisterCandidateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    full_name: str = Field(min_length=2, max_length=255)
    phone_number: str | None = Field(default=None, max_length=20)

    _check_password = field_validator("password")(_validate_password)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        cleaned = value.replace(" ", "").replace(".", "")
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError("Số điện thoại phải gồm 10-11 chữ số và bắt đầu bằng 0.")
        return cleaned


class CompanyRegistrationInfo(BaseModel):
    """Thông tin doanh nghiệp nhập lúc đăng ký tài khoản nhà tuyển dụng.

    Ở P1 nhập tay toàn bộ. P2 thêm nút tra cứu VietQR để tự điền company_name,
    international_name, short_name và headquarters_address.
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

    @field_validator("tax_code")
    @classmethod
    def validate_tax_code(cls, value: str) -> str:
        cleaned = value.strip().replace(" ", "")
        if not _TAX_CODE_PATTERN.match(cleaned):
            raise ValueError("Mã số thuế phải gồm 10 hoặc 13 chữ số.")
        return cleaned

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned = value.replace(" ", "").replace(".", "")
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError("Số điện thoại phải gồm 10-11 chữ số và bắt đầu bằng 0.")
        return cleaned


class RegisterEmployerRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    full_name: str = Field(min_length=2, max_length=255)
    phone_number: str | None = Field(default=None, max_length=20)
    company: CompanyRegistrationInfo

    _check_password = field_validator("password")(_validate_password)


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
