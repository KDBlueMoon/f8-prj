import uuid

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from middlewares.auth import require_role
from models.enums import UserRole
from models.job import Job, JobLocation
from models.user import User
from schemas.job import JobCreateRequest, JobDetailOut, job_to_out
from utils.db import transaction
from utils.sanitize import sanitize_rich_text
from utils.slug import slugify, unique_slug

router = APIRouter(prefix="/employer", tags=["Employer"])

SLUG_SUFFIX_LENGTH = 6


@router.post("/jobs", response_model=JobDetailOut, status_code=status.HTTP_201_CREATED)
@transaction
def create_job(
    payload: JobCreateRequest, current_user: User = Depends(require_role(UserRole.EMPLOYER))
) -> JobDetailOut:
    if current_user.company_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền truy cập")

    slug = unique_slug(payload.title, uuid.uuid4().hex[:SLUG_SUFFIX_LENGTH])
    salary = payload.salary

    job = Job.create(
        company_id=current_user.company_id,
        title=payload.title,
        slug=slug,
        category=payload.category,
        category_slug=slugify(payload.category),
        specialty=payload.specialty,
        job_type=payload.job_type,
        experience_level=payload.experience_level,
        gender=payload.gender,
        quantity=payload.quantity,
        salary_type=salary.type if salary else None,
        salary_min=salary.min if salary else None,
        salary_max=salary.max if salary else None,
        salary_currency=salary.currency if salary else "VND",
        salary_is_negotiable=salary.is_negotiable if salary else False,
        deadline=payload.deadline,
        is_hot=payload.is_hot,
        description_html=sanitize_rich_text(payload.description_html),
        requirements_html=sanitize_rich_text(payload.requirements_html)
        if payload.requirements_html
        else None,
        benefits_html=sanitize_rich_text(payload.benefits_html) if payload.benefits_html else None,
    )
    for loc in payload.work_location:
        JobLocation.create(
            job_id=job.id,
            city_id=loc.city_id,
            city_name=loc.city_name,
            address_detail=loc.address_detail,
        )

    return job_to_out(job)
