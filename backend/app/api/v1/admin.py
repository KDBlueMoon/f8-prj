import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.models.enums import CompanyStatus, JobStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.common import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page, build_page_meta
from app.schemas.company import (
    AdminCompanyDecisionIn,
    AdminUserOut,
    AdminUserStatusIn,
    AdminVerificationIn,
    CompanyListItemOut,
    CompanyOut,
)
from app.schemas.job import (
    AdminJobHotIn,
    AdminJobListItemOut,
    AdminJobTakedownIn,
    JobOut,
)
from app.services import company_service, job_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/companies", response_model=Page[CompanyListItemOut])
def list_companies(
    status_filter: CompanyStatus | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Page[CompanyListItemOut]:
    companies, total = company_service.list_companies(
        db, company_status=status_filter, keyword=q, page=page, page_size=page_size
    )
    return Page(
        items=[CompanyListItemOut.model_validate(company) for company in companies],
        meta=build_page_meta(page, page_size, total),
    )


@router.get("/companies/counts", response_model=dict[str, int])
def count_companies(
    _: User = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, int]:
    """Số hồ sơ theo từng trạng thái, để hiện badge trên tab."""
    return company_service.count_companies_by_status(db)


@router.get("/companies/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CompanyOut:
    return CompanyOut.model_validate(company_service.get_company_by_id(db, company_id))


@router.patch("/companies/{company_id}/status", response_model=CompanyOut)
def decide_company(
    company_id: uuid.UUID,
    payload: AdminCompanyDecisionIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CompanyOut:
    """Duyệt hoặc từ chối hồ sơ công ty. Từ chối bắt buộc kèm lý do."""
    company = company_service.get_company_by_id(db, company_id)
    updated = company_service.decide_company(
        db, company, new_status=payload.status, rejected_reason=payload.rejected_reason
    )
    return CompanyOut.model_validate(updated)


@router.patch("/companies/{company_id}/verification", response_model=CompanyOut)
def set_company_verification(
    company_id: uuid.UUID,
    payload: AdminVerificationIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CompanyOut:
    company = company_service.get_company_by_id(db, company_id)
    updated = company_service.set_verification(db, company, payload.verification_tier)
    return CompanyOut.model_validate(updated)


# ─────────────────────────── Giám sát tin tuyển dụng ───────────────────────────


@router.get("/jobs", response_model=Page[AdminJobListItemOut])
def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    company_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Page[AdminJobListItemOut]:
    """Toàn bộ tin của mọi công ty.

    Tin không qua bước duyệt nên đây là chốt giám sát duy nhất: admin thấy hết
    và gỡ được tin vi phạm (DESIGN mục 11.2).
    """
    jobs, total = job_service.list_jobs(
        db,
        job_status=status_filter,
        keyword=q,
        company_id=company_id,
        page=page,
        page_size=page_size,
    )
    return Page(
        items=[AdminJobListItemOut.model_validate(job) for job in jobs],
        meta=build_page_meta(page, page_size, total),
    )


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(
    job_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JobOut:
    return JobOut.model_validate(job_service.get_job_by_id(db, job_id))


@router.patch("/jobs/{job_id}/takedown", response_model=JobOut)
def take_down_job(
    job_id: uuid.UUID,
    payload: AdminJobTakedownIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JobOut:
    """Gỡ tin vi phạm. Lý do là bắt buộc để nhà tuyển dụng biết cần sửa gì."""
    job = job_service.get_job_by_id(db, job_id)
    return JobOut.model_validate(job_service.take_down_job(db, job, payload.takedown_reason))


@router.patch("/jobs/{job_id}/hot", response_model=JobOut)
def set_job_hot(
    job_id: uuid.UUID,
    payload: AdminJobHotIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JobOut:
    job = job_service.get_job_by_id(db, job_id)
    return JobOut.model_validate(job_service.set_job_hot(db, job, payload.is_hot))


@router.get("/users", response_model=Page[AdminUserOut])
def list_users(
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Page[AdminUserOut]:
    users, total = company_service.list_users(db, keyword=q, page=page, page_size=page_size)
    return Page(
        items=[AdminUserOut.model_validate(user) for user in users],
        meta=build_page_meta(page, page_size, total),
    )


@router.patch("/users/{user_id}/status", response_model=AdminUserOut)
def set_user_status(
    user_id: uuid.UUID,
    payload: AdminUserStatusIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserOut:
    updated = company_service.set_user_active(
        db, admin=admin, user_id=user_id, is_active=payload.is_active
    )
    return AdminUserOut.model_validate(updated)
