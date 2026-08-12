"""Dữ liệu danh mục dùng chung: tỉnh/thành, nhóm ngành, ngành nghề."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class City(Base):
    """34 tỉnh/thành sau sáp nhập 01/07/2025.

    id để int và cố định trong seed (1 = Hà Nội, 2 = TP.HCM) cho khớp
    quy ước city_id của data.json mẫu.
    """

    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # 6 thành phố trực thuộc TW — đẩy lên đầu dropdown chọn địa điểm.
    is_municipality: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CategoryGroup(Base, UUIDMixin, TimestampMixin):
    """Nhóm ngành, vd "Công nghệ Thông tin". Công ty gắn ở mức này."""

    __tablename__ = "category_groups"

    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # Thứ tự hiển thị do người vận hành quyết định. Không sắp theo tên vì
    # collation Postgres xử lý tiếng Việt có dấu không như mong đợi.
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    categories: Mapped[list["Category"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="Category.display_order",
    )


class Category(Base, UUIDMixin, TimestampMixin):
    """Ngành nghề cụ thể, vd "Lập trình phần mềm". Tin tuyển dụng gắn ở mức này."""

    __tablename__ = "categories"

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category_groups.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    group: Mapped["CategoryGroup"] = relationship(back_populates="categories")
