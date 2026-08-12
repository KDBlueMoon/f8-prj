"""Nghiệp vụ tin tuyển dụng.

Toàn bộ bất biến ở DESIGN mục 4.3 được ép ở tầng này chứ không ở frontend:
- Chỉ công ty `APPROVED` mới đăng được tin `PUBLISHED`.
- `TAKEN_DOWN` chỉ quản trị viên đặt được.
- Tin bị gỡ muốn lên lại phải sửa nội dung trước (xem `update_job`).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session, selectinload
from starlette import status as http_status

from app.core.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.db.models.catalog import Category, City
from app.db.models.company import Company
from app.db.models.enums import CompanyStatus, JobStatus, SalaryType
from app.db.models.job import Job, JobLocation
from app.db.models.user import User
from app.schemas.job import JobCreateIn, JobLocationIn, JobUpdateIn
from app.utils.slug import unique_slug

SLUG_SUFFIX_LENGTH = 6

# Nhà tuyển dụng được đi những đường nào. Bảng này là bản dịch trực tiếp của
# sơ đồ vòng đời trong DESIGN mục 4.3 — sửa luật thì sửa ở đúng một chỗ.
EMPLOYER_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.DRAFT: {JobStatus.PUBLISHED, JobStatus.CLOSED},
    JobStatus.PUBLISHED: {JobStatus.CLOSED},
    JobStatus.CLOSED: {JobStatus.PUBLISHED},
    JobStatus.EXPIRED: {JobStatus.PUBLISHED},
    # Rỗng có chủ đích: tin bị gỡ phải sửa nội dung mới về lại DRAFT.
    JobStatus.TAKEN_DOWN: set(),
}

# Số tiền lương bắt buộc / phải bỏ trống, theo từng kiểu lương.
_SALARY_FIELDS_REQUIRED: dict[SalaryType, tuple[str, ...]] = {
    SalaryType.RANGE: ("salary_min", "salary_max"),
    SalaryType.FROM: ("salary_min",),
    SalaryType.UP_TO: ("salary_max",),
    SalaryType.AGREEMENT: (),
}


# ─────────────────────────── Nhà tuyển dụng ───────────────────────────


def list_own_jobs(
    db: Session,
    company: Company,
    *,
    job_status: JobStatus | None,
    keyword: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Job], int]:
    stmt = _active_jobs().where(Job.company_id == company.id)
    stmt = _apply_job_filters(stmt, job_status, keyword)
    return _paginate(db, stmt, page=page, page_size=page_size)


def count_own_jobs_by_status(db: Session, company: Company) -> dict[str, int]:
    """Số tin theo từng trạng thái, để hiện badge trên các tab."""
    rows = db.execute(
        select(Job.status, func.count())
        .where(Job.company_id == company.id, Job.deleted_at.is_(None))
        .group_by(Job.status)
    ).all()
    counts = {item.value: 0 for item in JobStatus}
    for job_status, count in rows:
        counts[job_status.value] = count
    return counts


def get_own_job(db: Session, company: Company, job_id: uuid.UUID) -> Job:
    """Lấy tin của chính công ty đang đăng nhập.

    Điều kiện `company_id` nằm ngay trong câu truy vấn: đoán đúng id tin của
    công ty khác cũng chỉ nhận 404, không phải 403 — không lộ cả sự tồn tại.
    """
    job = db.scalar(
        _active_jobs()
        .where(Job.id == job_id, Job.company_id == company.id)
        .options(selectinload(Job.locations))
    )
    if job is None:
        raise NotFoundError("JOB_NOT_FOUND", "Không tìm thấy tin tuyển dụng này.")
    return job


def create_job(db: Session, company: Company, user: User, payload: JobCreateIn) -> Job:
    _validate_salary(payload.salary_type, payload.salary_min, payload.salary_max)
    _ensure_category_exists(db, payload.category_id)
    _ensure_cities_exist(db, payload.locations)

    if payload.status == JobStatus.PUBLISHED:
        _ensure_company_can_publish(company)

    job = Job(
        company_id=company.id,
        title=payload.title.strip(),
        # Hậu tố ngẫu nhiên: hai tin trùng tên vẫn ra hai slug khác nhau mà
        # không cần truy vấn kiểm tra trùng rồi thử lại.
        slug=unique_slug(payload.title, uuid.uuid4().hex[:SLUG_SUFFIX_LENGTH]),
        category_id=payload.category_id,
        specialty=payload.specialty,
        job_type=payload.job_type,
        experience_level=payload.experience_level,
        gender=payload.gender,
        quantity=payload.quantity,
        salary_type=payload.salary_type,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        deadline=payload.deadline,
        status=payload.status,
        description_html=payload.description_html,
        requirements_html=payload.requirements_html,
        benefits_html=payload.benefits_html,
        created_by=user.id,
        locations=_build_locations(payload.locations),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job(db: Session, job: Job, payload: JobUpdateIn) -> Job:
    """Sửa nội dung tin.

    Tin đang bị gỡ mà được sửa thì tự về `DRAFT` và xoá lý do gỡ — đó là cách
    duy nhất để tin bị gỡ quay lại: sửa rồi đăng lại. Cho phép bấm đăng lại
    ngay mà không sửa gì thì quyết định gỡ tin của quản trị viên vô nghĩa.
    """
    changes = payload.model_dump(exclude_unset=True, exclude={"locations"})
    if not changes and payload.locations is None:
        return job

    salary_type = changes.get("salary_type", job.salary_type)
    if "salary_type" in changes:
        # Đổi kiểu lương thì hai con số cũ có thể không còn dùng tới. Lấy đúng
        # những gì client gửi kèm lần này, phần không gửi coi như bỏ trống —
        # nếu giữ giá trị cũ thì đổi sang "thoả thuận" sẽ luôn bị báo lỗi.
        changes["salary_min"] = changes.get("salary_min")
        changes["salary_max"] = changes.get("salary_max")
    _validate_salary(
        salary_type,
        changes.get("salary_min", job.salary_min),
        changes.get("salary_max", job.salary_max),
    )
    if "category_id" in changes:
        _ensure_category_exists(db, changes["category_id"])

    for field, value in changes.items():
        setattr(job, field, value.strip() if field == "title" else value)

    if payload.locations is not None:
        _ensure_cities_exist(db, payload.locations)
        # Gán lại cả danh sách: cascade delete-orphan tự xoá địa điểm cũ.
        job.locations = _build_locations(payload.locations)

    if job.status == JobStatus.TAKEN_DOWN:
        job.status = JobStatus.DRAFT
        job.takedown_reason = None

    db.commit()
    db.refresh(job)
    return job


def change_status(db: Session, company: Company, job: Job, new_status: JobStatus) -> Job:
    if new_status not in EMPLOYER_TRANSITIONS[job.status]:
        raise _transition_error(job.status, new_status)

    if new_status == JobStatus.PUBLISHED:
        _ensure_company_can_publish(company)
        if job.deadline <= datetime.now(UTC):
            raise AppError(
                "JOB_DEADLINE_PASSED",
                "Hạn nộp hồ sơ đã qua. Hãy gia hạn trước khi đăng lại tin.",
            )

    job.status = new_status
    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job: Job) -> None:
    """Xoá mềm: lịch sử ứng tuyển của ứng viên phải còn đọc được sau khi gỡ tin."""
    job.deleted_at = datetime.now(UTC)
    db.commit()


# ─────────────────────────── Quản trị viên ───────────────────────────


def list_jobs(
    db: Session,
    *,
    job_status: JobStatus | None,
    keyword: str | None,
    company_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[Job], int]:
    stmt = _active_jobs().options(selectinload(Job.company))
    stmt = _apply_job_filters(stmt, job_status, keyword)
    if company_id is not None:
        stmt = stmt.where(Job.company_id == company_id)
    return _paginate(db, stmt, page=page, page_size=page_size)


def get_job_by_id(db: Session, job_id: uuid.UUID) -> Job:
    job = db.scalar(
        _active_jobs()
        .where(Job.id == job_id)
        .options(selectinload(Job.locations), selectinload(Job.company))
    )
    if job is None:
        raise NotFoundError("JOB_NOT_FOUND", "Không tìm thấy tin tuyển dụng này.")
    return job


def take_down_job(db: Session, job: Job, reason: str) -> Job:
    if job.status == JobStatus.TAKEN_DOWN:
        raise ConflictError("JOB_ALREADY_TAKEN_DOWN", "Tin này đã bị gỡ trước đó.")

    job.status = JobStatus.TAKEN_DOWN
    job.takedown_reason = reason.strip()
    db.commit()
    db.refresh(job)
    return job


def set_job_hot(db: Session, job: Job, is_hot: bool) -> Job:
    if is_hot and job.status != JobStatus.PUBLISHED:
        raise AppError(
            "JOB_NOT_PUBLISHED",
            "Chỉ gắn nhãn tin nổi bật cho tin đang được đăng.",
        )

    job.is_hot = is_hot
    db.commit()
    db.refresh(job)
    return job


def take_down_published_jobs(db: Session, company: Company, reason: str) -> int:
    """Gỡ toàn bộ tin đang đăng của một công ty. Trả về số tin bị gỡ.

    Cố ý KHÔNG commit: hàm này được gọi từ trong luồng từ chối hồ sơ công ty và
    phải nằm chung transaction với việc đổi trạng thái công ty. Nếu tách ra thì
    có khoảnh khắc công ty đã bị từ chối mà tin vẫn hiện trên trang công khai.
    """
    result = db.execute(
        update(Job)
        .where(
            Job.company_id == company.id,
            Job.status == JobStatus.PUBLISHED,
            Job.deleted_at.is_(None),
        )
        .values(status=JobStatus.TAKEN_DOWN, takedown_reason=reason)
    )
    return result.rowcount


# ─────────────────────────── Hàm dùng chung ───────────────────────────


def _active_jobs() -> Select:
    """Nền tảng cho mọi truy vấn: tin đã xoá mềm không bao giờ được trả ra."""
    return select(Job).where(Job.deleted_at.is_(None))


def _apply_job_filters(stmt: Select, job_status: JobStatus | None, keyword: str | None) -> Select:
    if job_status is not None:
        stmt = stmt.where(Job.status == job_status)
    if keyword:
        stmt = stmt.where(Job.title.ilike(f"%{keyword.strip()}%"))
    return stmt


def _paginate(db: Session, stmt: Select, *, page: int, page_size: int) -> tuple[list[Job], int]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Job.created_at.desc())
        .options(selectinload(Job.locations))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def _build_locations(payloads: list[JobLocationIn]) -> list[JobLocation]:
    return [
        JobLocation(
            city_id=item.city_id,
            address_detail=item.address_detail.strip() if item.address_detail else None,
        )
        for item in payloads
    ]


def _ensure_company_can_publish(company: Company) -> None:
    if company.status != CompanyStatus.APPROVED:
        raise ForbiddenError(
            "COMPANY_NOT_APPROVED",
            "Hồ sơ công ty chưa được duyệt nên chưa thể đăng tin. "
            "Bạn vẫn lưu được tin ở dạng nháp.",
        )


def _ensure_category_exists(db: Session, category_id: uuid.UUID) -> None:
    if db.get(Category, category_id) is None:
        raise NotFoundError("CATEGORY_NOT_FOUND", "Không tìm thấy ngành nghề đã chọn.")


def _ensure_cities_exist(db: Session, locations: list[JobLocationIn]) -> None:
    """Kiểm tra một lượt cho cả danh sách thay vì gọi `db.get` trong vòng lặp."""
    city_ids = {item.city_id for item in locations}
    found = set(db.scalars(select(City.id).where(City.id.in_(city_ids))).all())
    if city_ids - found:
        raise NotFoundError("CITY_NOT_FOUND", "Không tìm thấy tỉnh/thành đã chọn.")


def _validate_salary(
    salary_type: SalaryType, salary_min: int | None, salary_max: int | None
) -> None:
    """Ràng buộc chéo giữa kiểu lương và hai con số.

    Không đặt trong schema vì lúc PATCH chỉ có vài trường được gửi lên — luật
    phải chạy trên giá trị sau khi trộn với dữ liệu cũ, và đó là việc của service.
    """
    values = {"salary_min": salary_min, "salary_max": salary_max}
    required = _SALARY_FIELDS_REQUIRED[salary_type]

    for field in required:
        if values[field] is None:
            raise AppError("SALARY_REQUIRED", "Vui lòng nhập đủ mức lương cho kiểu lương đã chọn.")

    for field, value in values.items():
        if field not in required and value is not None:
            raise AppError(
                "SALARY_NOT_ALLOWED",
                "Kiểu lương đã chọn không dùng tới mức lương vừa nhập.",
            )

    if salary_min is not None and salary_max is not None and salary_max < salary_min:
        raise AppError("SALARY_RANGE_INVALID", "Lương tối đa phải lớn hơn hoặc bằng lương tối thiểu.")


def _transition_error(current: JobStatus, target: JobStatus) -> AppError:
    if current == JobStatus.TAKEN_DOWN:
        return AppError(
            "JOB_TAKEN_DOWN",
            "Tin đã bị quản trị viên gỡ. Hãy sửa lại nội dung tin, tin sẽ về dạng "
            "nháp và bạn đăng lại được.",
            http_status.HTTP_409_CONFLICT,
        )
    return ConflictError(
        "JOB_TRANSITION_INVALID",
        f"Không thể chuyển tin từ {current.value} sang {target.value}.",
    )
