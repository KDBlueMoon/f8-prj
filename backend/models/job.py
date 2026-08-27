import uuid
from datetime import datetime

from typing import Self

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, exists, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base, session
from models import ActiveRecordMixin, TimestampMixin, UUIDMixin
from models.company import Company
from models.enums import Gender, JobStatus, JobType, SalaryType


class JobLocation(Base, UUIDMixin, ActiveRecordMixin):
    """Một địa điểm làm việc trong `work_location` của tin tuyển dụng."""

    __tablename__ = "job_locations"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    city_id: Mapped[int | None] = mapped_column(Integer)
    city_name: Mapped[str | None] = mapped_column(String(255))
    address_detail: Mapped[str | None] = mapped_column(String(500))


class Job(Base, UUIDMixin, TimestampMixin, ActiveRecordMixin):
    __tablename__ = "jobs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # Lưu dạng string thuần theo đúng kiểu khai báo trong openapi.yaml, không
    # FK sang bảng category — job-taxonomy (`/categories`) là danh mục riêng.
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    # Sinh từ `category` lúc tạo — chỉ để lọc `GET /jobs?category_slug=`
    # (tham số này trong spec không đi kèm bảng category chuẩn hoá nào, job
    # chỉ lưu category dạng chuỗi tự do), không trả ra trong response.
    category_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    specialty: Mapped[str | None] = mapped_column(String(255))
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    experience_level: Mapped[str | None] = mapped_column(String(100))
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="gender", values_callable=lambda e: [i.value for i in e])
    )
    quantity: Mapped[int | None] = mapped_column(Integer)

    salary_type: Mapped[SalaryType | None] = mapped_column(
        Enum(SalaryType, name="salary_type", values_callable=lambda e: [i.value for i in e])
    )
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="VND")
    salary_is_negotiable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Không có endpoint nào đổi status sau khi tạo (spec không có PATCH/PUT job)
    # nên mặc định PUBLISHED ngay — để DRAFT sẽ không bao giờ hiển thị được.
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=JobStatus.PUBLISHED,
    )
    is_hot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description_html: Mapped[str] = mapped_column(Text, nullable=False)
    requirements_html: Mapped[str | None] = mapped_column(Text)
    benefits_html: Mapped[str | None] = mapped_column(Text)

    work_location: Mapped[list[JobLocation]] = relationship(
        cascade="all, delete-orphan", order_by="JobLocation.id"
    )
    company: Mapped[Company] = relationship()

    @classmethod
    def search(
        cls,
        *,
        keyword: str | None = None,
        category_slug: str | None = None,
        city_id: int | None = None,
        limit: int,
        offset: int,
    ) -> tuple[list[Self], int]:
        stmt = select(cls).where(cls.status == JobStatus.PUBLISHED)
        if keyword:
            stmt = stmt.where(cls.title.ilike(f"%{keyword}%"))
        if category_slug:
            stmt = stmt.where(cls.category_slug == category_slug)
        if city_id is not None:
            stmt = stmt.where(
                exists().where(JobLocation.job_id == cls.id, JobLocation.city_id == city_id)
            )

        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(cls.created_at.desc()).offset(offset).limit(limit)
        items = list(session.scalars(stmt).all())
        return items, total
