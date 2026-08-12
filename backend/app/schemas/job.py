"""Schema tin tuyển dụng.

HTML được làm sạch **ngay tại đây** bằng `AfterValidator`, không phải ở service:
mọi đường vào của dữ liệu đều đi qua schema, nên không có cách nào quên sanitize
khi sau này thêm endpoint mới.
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from app.db.models.enums import (
    ExperienceLevel,
    Gender,
    JobStatus,
    JobType,
    SalaryType,
    VerificationTier,
)
from app.utils.sanitize import MAX_RICH_TEXT_LENGTH, has_visible_text, sanitize_rich_text

MAX_QUANTITY = 999
# 100 tỷ: đủ chỗ cho mọi mức lương thật, đủ chặt để chặn số rác kiểu 10^18 làm
# tràn bigint hoặc vỡ giao diện.
MAX_SALARY = 100_000_000_000
MAX_LOCATIONS_PER_JOB = 10
MAX_TAKEDOWN_REASON_LENGTH = 1000

MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 255


def _clean_required_html(value: str) -> str:
    cleaned = sanitize_rich_text(value)
    if not has_visible_text(cleaned):
        raise ValueError("Nội dung không được để trống.")
    return cleaned


def _require_future(value: datetime) -> datetime:
    """Hạn nộp phải ở tương lai, và luôn quy về dạng có múi giờ.

    Client gửi thiếu offset thì coi như UTC — nếu để nguyên datetime "naive",
    mọi phép so sánh với `datetime.now(UTC)` về sau sẽ ném TypeError.
    """
    normalized = value if value.tzinfo else value.replace(tzinfo=UTC)
    if normalized <= datetime.now(UTC):
        raise ValueError("Hạn nộp hồ sơ phải ở tương lai.")
    return normalized


RichText = Annotated[
    str, Field(max_length=MAX_RICH_TEXT_LENGTH), AfterValidator(_clean_required_html)
]
FutureDeadline = Annotated[datetime, AfterValidator(_require_future)]


class JobLocationIn(BaseModel):
    city_id: int
    address_detail: str | None = Field(default=None, max_length=500)


class JobLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    city_id: int
    address_detail: str | None


class JobCreateIn(BaseModel):
    """Tạo tin mới.

    `status` chỉ nhận DRAFT hoặc PUBLISHED — tin không có bước chờ duyệt
    (DESIGN mục 4.3). Điều kiện để được PUBLISHED do service kiểm tra.
    """

    title: str = Field(min_length=MIN_TITLE_LENGTH, max_length=MAX_TITLE_LENGTH)
    category_id: uuid.UUID
    specialty: str | None = Field(default=None, max_length=255)

    job_type: JobType
    experience_level: ExperienceLevel
    gender: Gender = Gender.NOT_REQUIRED
    quantity: int = Field(default=1, ge=1, le=MAX_QUANTITY)

    salary_type: SalaryType
    salary_min: int | None = Field(default=None, ge=0, le=MAX_SALARY)
    salary_max: int | None = Field(default=None, ge=0, le=MAX_SALARY)

    deadline: FutureDeadline
    description_html: RichText
    requirements_html: RichText
    benefits_html: RichText

    locations: list[JobLocationIn] = Field(min_length=1, max_length=MAX_LOCATIONS_PER_JOB)
    status: JobStatus = JobStatus.DRAFT

    @field_validator("status")
    @classmethod
    def only_draft_or_published(cls, value: JobStatus) -> JobStatus:
        if value not in (JobStatus.DRAFT, JobStatus.PUBLISHED):
            raise ValueError("Tin mới chỉ có thể ở trạng thái DRAFT hoặc PUBLISHED.")
        return value


class JobUpdateIn(BaseModel):
    """Sửa tin — chỉ những trường được gửi lên mới bị thay đổi.

    Cố ý KHÔNG cho sửa `status` ở đây: đổi trạng thái đi qua endpoint riêng để
    luật chuyển trạng thái nằm gọn một chỗ. Cũng không cho sửa `slug` vì slug đã
    nằm trong URL công khai, đổi là gãy mọi link đã chia sẻ.
    """

    title: str | None = Field(default=None, min_length=MIN_TITLE_LENGTH, max_length=MAX_TITLE_LENGTH)
    category_id: uuid.UUID | None = None
    specialty: str | None = Field(default=None, max_length=255)

    job_type: JobType | None = None
    experience_level: ExperienceLevel | None = None
    gender: Gender | None = None
    quantity: int | None = Field(default=None, ge=1, le=MAX_QUANTITY)

    salary_type: SalaryType | None = None
    salary_min: int | None = Field(default=None, ge=0, le=MAX_SALARY)
    salary_max: int | None = Field(default=None, ge=0, le=MAX_SALARY)

    deadline: FutureDeadline | None = None
    description_html: RichText | None = None
    requirements_html: RichText | None = None
    benefits_html: RichText | None = None

    locations: list[JobLocationIn] | None = Field(
        default=None, min_length=1, max_length=MAX_LOCATIONS_PER_JOB
    )


class JobStatusIn(BaseModel):
    status: JobStatus

    @field_validator("status")
    @classmethod
    def only_employer_statuses(cls, value: JobStatus) -> JobStatus:
        """TAKEN_DOWN và EXPIRED không nằm trong tay nhà tuyển dụng.

        TAKEN_DOWN là quyết định của quản trị viên, EXPIRED do hệ thống đặt khi
        quá hạn — NTD tự đặt được thì hai trạng thái đó mất hết ý nghĩa.
        """
        if value not in (JobStatus.PUBLISHED, JobStatus.CLOSED):
            raise ValueError("Chỉ được chuyển sang PUBLISHED hoặc CLOSED.")
        return value


class JobCompanyBriefOut(BaseModel):
    """Company rút gọn nhúng trong tin — đủ để hiển thị thẻ tin, không hơn."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    short_name: str | None
    slug: str
    logo_url: str | None
    verification_tier: VerificationTier


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    slug: str
    category_id: uuid.UUID
    specialty: str | None

    job_type: JobType
    experience_level: ExperienceLevel
    gender: Gender
    quantity: int

    salary_type: SalaryType
    salary_min: int | None
    salary_max: int | None
    currency: str

    deadline: datetime
    status: JobStatus
    takedown_reason: str | None
    is_hot: bool
    view_count: int

    description_html: str
    requirements_html: str
    benefits_html: str

    created_at: datetime
    updated_at: datetime
    locations: list[JobLocationOut]


class JobListItemOut(BaseModel):
    """Bản rút gọn cho màn hình danh sách — bỏ 3 khối HTML dài."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    category_id: uuid.UUID
    job_type: JobType
    experience_level: ExperienceLevel
    quantity: int

    salary_type: SalaryType
    salary_min: int | None
    salary_max: int | None
    currency: str

    deadline: datetime
    status: JobStatus
    takedown_reason: str | None
    is_hot: bool
    view_count: int
    created_at: datetime
    locations: list[JobLocationOut]


class AdminJobListItemOut(JobListItemOut):
    """Admin xem tin của mọi công ty nên cần biết tin thuộc về ai."""

    company: JobCompanyBriefOut


class AdminJobTakedownIn(BaseModel):
    takedown_reason: str = Field(min_length=5, max_length=MAX_TAKEDOWN_REASON_LENGTH)


class AdminJobHotIn(BaseModel):
    is_hot: bool
