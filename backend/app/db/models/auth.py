import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    """Sổ theo dõi refresh token đang phát hành, để logout thu hồi được token.

    Chỉ lưu `jti` (id của token) chứ không lưu chuỗi token: rò rỉ bảng này cũng
    không cho phép ai đăng nhập thay người dùng.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Đặt khi người dùng logout hoặc khi token được luân chuyển (rotate).
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
