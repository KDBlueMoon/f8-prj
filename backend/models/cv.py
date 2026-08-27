import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from models import ActiveRecordMixin, TimestampMixin, UUIDMixin


class CV(Base, UUIDMixin, TimestampMixin, ActiveRecordMixin):
    __tablename__ = "cvs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    education: Mapped[list | None] = mapped_column(JSONB)
    experience: Mapped[list | None] = mapped_column(JSONB)
    skills: Mapped[list | None] = mapped_column(JSONB)
