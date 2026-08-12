"""Endpoint tin tuyển dụng công khai — khách chưa đăng nhập gọi được.

Không có dependency xác thực nào ở đây là cố ý (DESIGN mục 5.2). Bù lại, mọi
truy vấn đều đi qua `job_service._visible_to_public()` nên tin nháp, tin đã
đóng, tin bị gỡ hay tin của công ty chưa duyệt không có đường nào lọt ra.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import Page, build_page_meta
from app.schemas.public import PublicJobDetailOut, PublicJobFilters, PublicJobListItemOut
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])

MAX_SLUG_LENGTH = 300


@router.get("", response_model=Page[PublicJobListItemOut])
def list_jobs(
    # FastAPI trải các trường của model thành từng query param riêng — nhờ vậy
    # contract ở mục 5.3 chỉ phải khai báo một chỗ (schemas/public.py).
    filters: Annotated[PublicJobFilters, Query()],
    db: Session = Depends(get_db),
) -> Page[PublicJobListItemOut]:
    """Danh sách việc làm kèm bộ lọc, sắp xếp và phân trang."""
    jobs, total = job_service.list_public_jobs(db, filters)
    return Page(
        items=[PublicJobListItemOut.model_validate(job) for job in jobs],
        meta=build_page_meta(filters.page, filters.page_size, total),
    )


@router.get("/{slug}", response_model=PublicJobDetailOut)
def get_job(
    slug: str = Path(min_length=1, max_length=MAX_SLUG_LENGTH),
    db: Session = Depends(get_db),
) -> PublicJobDetailOut:
    """Chi tiết tin theo slug, kèm object công ty lồng vào.

    Dùng slug chứ không dùng id: URL đọc được và tốt cho SEO — đó cũng là lý do
    slug không đổi khi nhà tuyển dụng sửa tiêu đề tin.
    """
    return PublicJobDetailOut.model_validate(job_service.get_public_job_by_slug(db, slug))
