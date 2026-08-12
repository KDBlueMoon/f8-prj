from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class Page(BaseModel, Generic[T]):
    """Bọc chung cho mọi endpoint trả danh sách, để FE xử lý đồng nhất."""

    items: list[T]
    meta: PageMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
