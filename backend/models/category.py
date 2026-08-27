import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base
from models import ActiveRecordMixin, UUIDMixin


class CategoryGroup(Base, UUIDMixin, ActiveRecordMixin):
    __tablename__ = "category_groups"

    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    categories: Mapped[list["Category"]] = relationship(
        back_populates="group", order_by="Category.display_order"
    )


class Category(Base, UUIDMixin, ActiveRecordMixin):
    __tablename__ = "categories"

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category_groups.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    group: Mapped[CategoryGroup] = relationship(back_populates="categories")
