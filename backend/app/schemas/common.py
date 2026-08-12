from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


def build_page_meta(page: int, page_size: int, total: int) -> PageMeta:
    # Chia lên: 21 bản ghi với page_size 20 là 2 trang.
    total_pages = (total + page_size - 1) // page_size
    return PageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)


class Page(BaseModel, Generic[T]):
    """Bọc chung cho mọi endpoint trả danh sách, để FE xử lý đồng nhất."""

    items: list[T]
    meta: PageMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
