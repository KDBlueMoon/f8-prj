import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from app.core.deps import require_employer
from app.db.models.enums import JobStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.common import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page, build_page_meta
from app.schemas.company import (
    CompanyAddressIn,
    CompanyAddressOut,
    CompanyOut,
    CompanyUpdateIn,
)
from app.schemas.job import (
    JobCreateIn,
    JobListItemOut,
    JobOut,
    JobStatusIn,
    JobUpdateIn,
)
from app.services import company_service, job_service

router = APIRouter(prefix="/employer", tags=["employer"])


@router.get("/company", response_model=CompanyOut)
def get_my_company(
    user: User = Depends(require_employer), db: Session = Depends(get_db)
) -> CompanyOut:
    """Hồ sơ công ty của chính tài khoản đang đăng nhập.

    Không nhận company_id từ client: công ty được suy ra từ token, nên không có
    cách nào xem hồ sơ của công ty khác.
    """
    return CompanyOut.model_validate(company_service.get_own_company(db, user))


@router.patch("/company", response_model=CompanyOut)
def update_my_company(
    payload: CompanyUpdateIn,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> CompanyOut:
    company = company_service.get_own_company(db, user)
    return CompanyOut.model_validate(company_service.update_own_company(db, company, payload))


@router.post(
    "/company/addresses", response_model=CompanyAddressOut, status_code=status.HTTP_201_CREATED
)
def add_company_address(
    payload: CompanyAddressIn,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> CompanyAddressOut:
    company = company_service.get_own_company(db, user)
    return CompanyAddressOut.model_validate(company_service.add_address(db, company, payload))


@router.delete("/company/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_address(
    address_id: uuid.UUID,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> None:
    company = company_service.get_own_company(db, user)
    company_service.delete_address(db, company, address_id)


# ─────────────────────────── Tin tuyển dụng ───────────────────────────


@router.get("/jobs", response_model=Page[JobListItemOut])
def list_my_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> Page[JobListItemOut]:
    """Tin của chính công ty mình, mọi trạng thái."""
    company = company_service.get_own_company(db, user)
    jobs, total = job_service.list_own_jobs(
        db, company, job_status=status_filter, keyword=q, page=page, page_size=page_size
    )
    return Page(
        items=[JobListItemOut.model_validate(job) for job in jobs],
        meta=build_page_meta(page, page_size, total),
    )


@router.get("/jobs/counts", response_model=dict[str, int])
def count_my_jobs(
    user: User = Depends(require_employer), db: Session = Depends(get_db)
) -> dict[str, int]:
    company = company_service.get_own_company(db, user)
    return job_service.count_own_jobs_by_status(db, company)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_my_job(
    job_id: uuid.UUID,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> JobOut:
    company = company_service.get_own_company(db, user)
    return JobOut.model_validate(job_service.get_own_job(db, company, job_id))


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreateIn,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> JobOut:
    """Tạo tin mới.

    Gửi `status=PUBLISHED` mà công ty chưa được duyệt sẽ nhận
    `COMPANY_NOT_APPROVED` — tin không được lặng lẽ hạ xuống nháp, vì nhà tuyển
    dụng cần biết rõ tin của mình chưa lên.
    """
    company = company_service.get_own_company(db, user)
    return JobOut.model_validate(job_service.create_job(db, company, user, payload))


@router.patch("/jobs/{job_id}", response_model=JobOut)
def update_job(
    job_id: uuid.UUID,
    payload: JobUpdateIn,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> JobOut:
    company = company_service.get_own_company(db, user)
    job = job_service.get_own_job(db, company, job_id)
    return JobOut.model_validate(job_service.update_job(db, job, payload))


@router.patch("/jobs/{job_id}/status", response_model=JobOut)
def change_job_status(
    job_id: uuid.UUID,
    payload: JobStatusIn,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> JobOut:
    company = company_service.get_own_company(db, user)
    job = job_service.get_own_job(db, company, job_id)
    return JobOut.model_validate(job_service.change_status(db, company, job, payload.status))


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: uuid.UUID,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> None:
    company = company_service.get_own_company(db, user)
    job_service.delete_job(db, job_service.get_own_job(db, company, job_id))
