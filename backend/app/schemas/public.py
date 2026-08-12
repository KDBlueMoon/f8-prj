"""Schema cho các endpoint công khai (khách chưa đăng nhập cũng gọi được).

Tách riêng khỏi `job.py`/`company.py` vì đây là những shape **trộn** cả hai
(job lồng company, company lồng danh sách job) — để chung sẽ thành import vòng.

Nguyên tắc: schema ở đây quyết định cái gì lộ ra internet. Không kế thừa từ
schema nội bộ để tránh trường hợp sau này thêm một cột nhạy cảm vào schema cha
rồi vô tình phơi ra ngoài mà không ai nhận ra.
"""

import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import (
    CompanySize,
    ExperienceLevel,
    Gender,
    JobType,
    SalaryType,
    VerificationTier,
)
from app.schemas.common import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.schemas.job import JobCompanyBriefOut, JobLocationOut

MAX_KEYWORD_LENGTH = 100
# Trang công ty hiển thị hết tin đang tuyển; chặn trên để một công ty đăng vài
# nghìn tin không kéo sập trang.
MAX_JOBS_ON_COMPANY_PAGE = 50


class JobSort(str, Enum):
    NEWEST = "newest"
    SALARY_DESC = "salary_desc"
    DEADLINE = "deadline"


class PublicJobFilters(BaseModel):
    """Toàn bộ tham số của `GET /jobs` (DESIGN mục 5.3).

    Gom vào một model thay vì 12 tham số rời: FastAPI vẫn nhận đúng từng query
    param, còn service chỉ nhận một đối tượng nên thêm bộ lọc mới không phải sửa
    chữ ký hàm ở cả hai nơi.
    """

    q: str | None = Field(default=None, max_length=MAX_KEYWORD_LENGTH)
    category_id: uuid.UUID | None = None
    group_id: uuid.UUID | None = None
    city_id: int | None = None
    job_type: JobType | None = None
    experience_level: ExperienceLevel | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    is_hot: bool | None = None
    sort: JobSort = JobSort.NEWEST
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)


class PublicCompanyAddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    city_id: int
    address_detail: str


class PublicCompanyOut(BaseModel):
    """Hồ sơ công ty ở góc nhìn người ngoài.

    Cố ý KHÔNG có `email`, `phone_number`, `director`, `tax_code`,
    `rejected_reason`, `status`:
    - Email và số điện thoại phơi ra là mời bot thu thập để gửi rác; ứng viên
      liên hệ qua chính chức năng ứng tuyển, không cần địa chỉ liên hệ trực tiếp.
    - `rejected_reason` là ghi chú nội bộ giữa quản trị viên và nhà tuyển dụng.
    - Chỉ công ty `APPROVED` mới xuất hiện ở đây nên `status` luôn cùng một giá
      trị, trả ra chỉ tổ gợi ý rằng có những trạng thái khác.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    international_name: str | None
    short_name: str | None
    slug: str
    headquarters_address: str
    issued_date: date | None
    website: str | None
    logo_url: str | None
    company_size: CompanySize
    category_group_id: uuid.UUID | None
    description_html: str | None
    verification_tier: VerificationTier
    created_at: datetime
    addresses: list[PublicCompanyAddressOut]


class PublicJobListItemOut(BaseModel):
    """Thẻ tin trên trang danh sách — company rút gọn để payload nhẹ."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    category_id: uuid.UUID
    specialty: str | None
    job_type: JobType
    experience_level: ExperienceLevel
    quantity: int

    salary_type: SalaryType
    salary_min: int | None
    salary_max: int | None
    currency: str

    deadline: datetime
    is_hot: bool
    view_count: int
    created_at: datetime

    locations: list[JobLocationOut]
    company: JobCompanyBriefOut


class PublicJobDetailOut(BaseModel):
    """Chi tiết tin, kèm object company đầy đủ lồng vào như `data.json` mẫu."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
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
    is_hot: bool
    view_count: int

    description_html: str
    requirements_html: str
    benefits_html: str

    created_at: datetime
    updated_at: datetime

    locations: list[JobLocationOut]
    company: PublicCompanyOut


class PublicCompanyCardOut(BaseModel):
    """Phần đọc thẳng được từ bản ghi công ty."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    short_name: str | None
    slug: str
    logo_url: str | None
    company_size: CompanySize
    category_group_id: uuid.UUID | None
    verification_tier: VerificationTier


class PublicCompanyListItemOut(PublicCompanyCardOut):
    # Số tin đang tuyển đến từ subquery đếm, không phải cột trên bảng — nên tách
    # ra lớp con để phần còn lại vẫn `model_validate` thẳng từ ORM được.
    open_job_count: int


class PublicCompanyDetailOut(PublicCompanyOut):
    """Trang công ty: hồ sơ + toàn bộ tin đang tuyển.

    Gộp vào một response thay vì bắt frontend gọi hai lượt — trang này luôn cần
    cả hai, tách ra chỉ thêm một vòng round-trip.
    """

    open_jobs: list[PublicJobListItemOut]
