from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.models.enums import UserRole


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    # CITEXT: email không phân biệt hoa/thường ngay ở tầng DB, nên UNIQUE
    # chặn được cả "A@x.com" lẫn "a@x.com".
    email: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True, index=True)
    # bcrypt hash — không bao giờ trả ra API, không bao giờ ghi log.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
