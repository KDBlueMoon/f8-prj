import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from models.enums import Gender, JobStatus, JobType, SalaryType
from models.job import Job
from schemas.common import Address
from schemas.company import CompanyOut


class SalaryIn(BaseModel):
    type: SalaryType | None = None
    min: int | None = None
    max: int | None = None
    currency: str = "VND"
    is_negotiable: bool = False


class SalaryOut(BaseModel):
    type: SalaryType | None
    min: int | None
    max: int | None
    currency: str
    is_negotiable: bool


class JobCreateRequest(BaseModel):
    title: str
    category: str
    specialty: str | None = None
    job_type: JobType
    experience_level: str | None = None
    gender: Gender | None = None
    quantity: int | None = None
    salary: SalaryIn | None = None
    work_location: list[Address] = Field(default_factory=list)
    deadline: datetime
    is_hot: bool = False
    description_html: str
    requirements_html: str | None = None
    benefits_html: str | None = None


class JobDetailOut(BaseModel):
    id: uuid.UUID
    company: CompanyOut
    title: str
    slug: str
    category: str
    specialty: str | None
    job_type: JobType
    experience_level: str | None
    gender: Gender | None
    quantity: int | None
    salary: SalaryOut
    work_location: list[Address]
    deadline: datetime
    status: JobStatus
    is_hot: bool
    description_html: str
    requirements_html: str | None
    benefits_html: str | None


def job_to_out(job: Job) -> JobDetailOut:
    """`Job` ORM object -> `JobDetailOut`.

    Không dùng `model_validate(job, from_attributes=True)` trực tiếp vì
    `salary` là field lồng trong response nhưng lại là các cột phẳng
    (`salary_type`, `salary_min`, ...) trên model — phải gom tay.
    """
    return JobDetailOut(
        id=job.id,
        company=CompanyOut.model_validate(job.company),
        title=job.title,
        slug=job.slug,
        category=job.category,
        specialty=job.specialty,
        job_type=job.job_type,
        experience_level=job.experience_level,
        gender=job.gender,
        quantity=job.quantity,
        salary=SalaryOut(
            type=job.salary_type,
            min=job.salary_min,
            max=job.salary_max,
            currency=job.salary_currency,
            is_negotiable=job.salary_is_negotiable,
        ),
        work_location=[Address.model_validate(loc) for loc in job.work_location],
        deadline=job.deadline,
        status=job.status,
        is_hot=job.is_hot,
        description_html=job.description_html,
        requirements_html=job.requirements_html,
        benefits_html=job.benefits_html,
    )
