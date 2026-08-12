import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.models.company import Company
from app.db.models.enums import ExperienceLevel, Gender, JobStatus, JobType, SalaryType


def _enum(py_enum, name: str) -> Enum:
    return Enum(py_enum, name=name, values_callable=lambda e: [i.value for i in e])


class Job(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_jobs_quantity_positive"),
        CheckConstraint(
            "salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min",
            name="ck_jobs_salary_range",
        ),
        # Truy vấn công khai luôn lọc theo cặp này -> index chung cho rẻ.
        Index("ix_jobs_status_deadline", "status", "deadline"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), nullable=False, unique=True, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    specialty: Mapped[str | None] = mapped_column(String(255))

    job_type: Mapped[JobType] = mapped_column(_enum(JobType, "job_type"), nullable=False)
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        _enum(ExperienceLevel, "experience_level"), nullable=False
    )
    gender: Mapped[Gender] = mapped_column(
        _enum(Gender, "gender"), nullable=False, default=Gender.NOT_REQUIRED
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    salary_type: Mapped[SalaryType] = mapped_column(_enum(SalaryType, "salary_type"), nullable=False)
    # NULL khi thoả thuận — cố ý không dùng 0 để khỏi nhầm với "lương 0đ".
    salary_min: Mapped[int | None] = mapped_column(BigInteger)
    salary_max: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="VND")

    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        _enum(JobStatus, "job_status"), nullable=False, default=JobStatus.DRAFT
    )
    takedown_reason: Mapped[str | None] = mapped_column(Text)
    is_hot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    description_html: Mapped[str] = mapped_column(Text, nullable=False)
    requirements_html: Mapped[str] = mapped_column(Text, nullable=False)
    benefits_html: Mapped[str] = mapped_column(Text, nullable=False)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    locations: Mapped[list["JobLocation"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    # Một chiều: màn hình admin cần biết tin thuộc công ty nào, nhưng Company
    # không cần danh sách job (luôn truy vấn kèm phân trang và bộ lọc).
    company: Mapped[Company] = relationship()


class JobLocation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "job_locations"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    address_detail: Mapped[str | None] = mapped_column(Text)

    job: Mapped["Job"] = relationship(back_populates="locations")
