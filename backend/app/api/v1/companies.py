import uuid

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.integrations import vietqr
from app.schemas.common import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page, build_page_meta
from app.schemas.company import TaxCodeLookupOut
from app.schemas.public import (
    MAX_JOBS_ON_COMPANY_PAGE,
    MAX_KEYWORD_LENGTH,
    PublicCompanyCardOut,
    PublicCompanyDetailOut,
    PublicCompanyListItemOut,
    PublicCompanyOut,
    PublicJobListItemOut,
)
from app.schemas.validators import validate_tax_code
from app.services import company_service, job_service

router = APIRouter(prefix="/companies", tags=["companies"])

MAX_SLUG_LENGTH = 255


@router.get("/lookup-tax-code/{tax_code}", response_model=TaxCodeLookupOut)
@limiter.limit("10/minute")
def lookup_tax_code(
    request: Request,
    tax_code: str = Path(min_length=10, max_length=14),
) -> TaxCodeLookupOut:
    """Tra cứu doanh nghiệp theo mã số thuế để tự điền form đăng ký.

    Công khai vì người dùng cần dùng trước khi có tài khoản. Có giới hạn tần
    suất để không biến endpoint này thành công cụ quét dữ liệu doanh nghiệp
    hàng loạt qua hệ thống của mình.

    Chỉ trả 4 trường VietQR có. Người đại diện, số điện thoại, email, ngày cấp,
    quy mô và lĩnh vực phải nhập tay.
    """
    try:
        cleaned_tax_code = validate_tax_code(tax_code)
    except ValueError as error:
        # Mã số thuế nằm trên đường dẫn nên Pydantic không kiểm hộ được như với
        # body — phải tự chuyển lỗi sang format lỗi chung của hệ thống.
        raise AppError("INVALID_TAX_CODE", str(error)) from error

    info = vietqr.lookup_tax_code(cleaned_tax_code)
    return TaxCodeLookupOut(
        tax_code=info.tax_code,
        company_name=info.company_name,
        international_name=info.international_name,
        short_name=info.short_name,
        headquarters_address=info.headquarters_address,
    )


@router.get("", response_model=Page[PublicCompanyListItemOut])
def list_companies(
    q: str | None = Query(default=None, max_length=MAX_KEYWORD_LENGTH),
    group_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
) -> Page[PublicCompanyListItemOut]:
    """Danh sách công ty đã được duyệt, kèm số tin đang tuyển."""
    rows, total = company_service.list_public_companies(
        db, keyword=q, group_id=group_id, page=page, page_size=page_size
    )
    return Page(
        items=[
            PublicCompanyListItemOut(
                **PublicCompanyCardOut.model_validate(company).model_dump(),
                open_job_count=open_job_count,
            )
            for company, open_job_count in rows
        ],
        meta=build_page_meta(page, page_size, total),
    )


@router.get("/{slug}", response_model=PublicCompanyDetailOut)
def get_company(
    slug: str = Path(min_length=1, max_length=MAX_SLUG_LENGTH),
    db: Session = Depends(get_db),
) -> PublicCompanyDetailOut:
    """Trang công ty: hồ sơ + toàn bộ tin đang tuyển.

    Không trả email, số điện thoại hay người đại diện — xem lý do ở
    `schemas/public.py::PublicCompanyOut`.
    """
    company = company_service.get_public_company_by_slug(db, slug)
    open_jobs = job_service.list_open_jobs_of_company(
        db, company.id, limit=MAX_JOBS_ON_COMPANY_PAGE
    )
    return PublicCompanyDetailOut(
        **PublicCompanyOut.model_validate(company).model_dump(),
        open_jobs=[PublicJobListItemOut.model_validate(job) for job in open_jobs],
    )
