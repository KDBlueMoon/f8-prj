import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from middlewares.auth import require_role
from models.application import Application
from models.cv import CV
from models.enums import JobStatus, UserRole
from models.job import Job
from models.user import User
from schemas.application import ApplyJobRequest
from schemas.job import JobDetailOut, job_to_out
from utils.db import transaction

router = APIRouter(tags=["Public"])

PAGE_SIZE = 20


@router.get("/jobs")
def list_jobs(
    page: int = Query(1, ge=1),
    keyword: str | None = None,
    category_slug: str | None = None,
    city_id: int | None = None,
) -> dict:
    items, total = Job.search(
        keyword=keyword,
        category_slug=category_slug,
        city_id=city_id,
        limit=PAGE_SIZE,
        offset=(page - 1) * PAGE_SIZE,
    )
    return {"data": [job_to_out(job) for job in items], "total": total}


@router.get("/jobs/{slug}", response_model=JobDetailOut)
def get_job(slug: str) -> JobDetailOut:
    matches = Job.get_list(slug=slug)
    job = matches[0] if matches else None
    if job is None or job.status != JobStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy job")
    return job_to_out(job)


@router.post("/jobs/{id}/apply", tags=["Candidate"], status_code=status.HTTP_200_OK)
@transaction
def apply_job(
    id: uuid.UUID,
    payload: ApplyJobRequest,
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> dict:
    job = Job.get_by_id(id)
    if job is None or job.status != JobStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy job")

    cv = CV.get_by_id(payload.cv_id)
    if cv is None or cv.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy CV")

    Application.create(
        job_id=job.id,
        candidate_id=current_user.id,
        cv_id=cv.id,
        cover_letter=payload.cover_letter,
    )
    return {"message": "Apply thành công"}
