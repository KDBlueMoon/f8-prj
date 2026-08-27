import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from models import ActiveRecordMixin, TimestampMixin, UUIDMixin


class Application(Base, UUIDMixin, TimestampMixin, ActiveRecordMixin):
    """Một lượt ứng viên apply vào một job."""

    __tablename__ = "applications"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    cv_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cvs.id"), nullable=False)
    cover_letter: Mapped[str | None] = mapped_column(Text)
