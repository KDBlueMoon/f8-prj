import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.models.enums import ApplicationStatus

MAX_COVER_LETTER_LENGTH = 2000


class Cv(Base, UUIDMixin, TimestampMixin):
    """CV dạng PDF của ứng viên, lưu trên S3 bucket private."""

    __tablename__ = "cvs"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Key nội bộ trên S3 (cvs/{candidate_id}/{uuid}.pdf) — không phải URL public.
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    # Tên file người dùng đặt, chỉ để hiển thị. Luôn escape khi render.
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Application(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        # Chặn apply trùng ngay ở tầng DB, không chỉ dựa vào check trong code.
        UniqueConstraint("job_id", "candidate_id", name="uq_applications_job_candidate"),
        CheckConstraint(
            f"cover_letter IS NULL OR length(cover_letter) <= {MAX_COVER_LETTER_LENGTH}",
            name="ck_applications_cover_letter_length",
        ),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # RESTRICT: không cho xoá CV đang gắn với hồ sơ đã nộp.
    cv_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cvs.id", ondelete="RESTRICT"), nullable=False
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=ApplicationStatus.PENDING,
    )


class SavedJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
