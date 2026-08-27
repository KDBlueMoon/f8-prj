import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from models import ActiveRecordMixin, TimestampMixin, UUIDMixin
from models.enums import UserRole


class User(Base, UUIDMixin, TimestampMixin, ActiveRecordMixin):
    __tablename__ = "users"

    # CITEXT: email không phân biệt hoa/thường ngay ở tầng DB.
    email: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Chỉ set khi role=EMPLOYER — tài khoản đại diện cho công ty nào.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
