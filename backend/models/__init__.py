"""Base ActiveRecord tối giản: model tự có get/create/update/delete, router gọi thẳng.

Đủ cho quy mô ~10 endpoint của API này — không cần bộ filter/pagination DSL
tổng quát.
"""

import uuid
from datetime import datetime
from typing import Any, Self

from sqlalchemy import DateTime, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base, session


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ActiveRecordMixin:
    """Trộn vào model cùng `Base`/`UUIDMixin` để có sẵn vài thao tác CRUD cơ bản."""

    @classmethod
    def get_by_id(cls, id_: Any) -> Self | None:
        return session.get(cls, id_)

    @classmethod
    def get_list(
        cls,
        *,
        order_by: Any = None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> list[Self]:
        stmt = select(cls)
        for field, value in filters.items():
            stmt = stmt.where(getattr(cls, field) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(session.scalars(stmt).all())

    @classmethod
    def count(cls, **filters: Any) -> int:
        stmt = select(func.count()).select_from(cls)
        for field, value in filters.items():
            stmt = stmt.where(getattr(cls, field) == value)
        return session.scalar(stmt) or 0

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        obj = cls(**kwargs)
        session.add(obj)
        session.flush()
        return obj

    def update(self, **kwargs: Any) -> Self:
        for field, value in kwargs.items():
            setattr(self, field, value)
        session.flush()
        return self
