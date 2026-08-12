"""Nghiệp vụ hồ sơ công ty và luồng duyệt của quản trị viên."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload
from starlette import status

from app.core.errors import AppError, ConflictError, NotFoundError
from app.db.models.catalog import City
from app.db.models.company import Company, CompanyAddress, CompanyMember
from app.db.models.enums import CompanyStatus, JobStatus, VerificationTier
from app.db.models.job import Job
from app.db.models.user import User
from app.integrations import vietqr
from app.schemas.company import CompanyAddressIn, CompanyUpdateIn
from app.services import job_service

MAX_ADDRESSES_PER_COMPANY = 10


def get_own_company(db: Session, user: User) -> Company:
    """Lấy công ty của nhà tuyển dụng đang đăng nhập.

    Mọi endpoint của nhà tuyển dụng đều đi qua đây, nên không có đường nào chạm
    tới công ty của người khác — đó là cách chặn IDOR ở tầng nghiệp vụ.
    """
    company = db.scalar(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(CompanyMember.user_id == user.id, Company.deleted_at.is_(None))
        .options(selectinload(Company.addresses))
    )
    if company is None:
        raise NotFoundError(
            "COMPANY_NOT_FOUND",
            "Tài khoản của bạn chưa gắn với công ty nào.",
        )
    return company


def update_own_company(db: Session, company: Company, payload: CompanyUpdateIn) -> Company:
    """Cập nhật hồ sơ công ty.

    Hồ sơ đã bị từ chối mà sửa lại thì tự đưa về PENDING để admin duyệt lượt
    mới — nếu không, nhà tuyển dụng sửa xong sẽ mắc kẹt ở trạng thái REJECTED
    mà không có cách nào gửi lại.
    """
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(company, field, value)

    if changes and company.status == CompanyStatus.REJECTED:
        company.status = CompanyStatus.PENDING
        company.rejected_reason = None

    # Tên công ty đổi thì kết quả đối chiếu VietQR cũ không còn giá trị.
    if "company_name" in changes:
        company.tax_code_verified_at = None

    db.commit()
    db.refresh(company)
    return company


def add_address(db: Session, company: Company, payload: CompanyAddressIn) -> CompanyAddress:
    if db.get(City, payload.city_id) is None:
        raise NotFoundError("CITY_NOT_FOUND", "Không tìm thấy tỉnh/thành đã chọn.")

    if len(company.addresses) >= MAX_ADDRESSES_PER_COMPANY:
        raise ConflictError(
            "ADDRESS_LIMIT_REACHED",
            f"Mỗi công ty chỉ được khai tối đa {MAX_ADDRESSES_PER_COMPANY} địa chỉ.",
        )

    address = CompanyAddress(
        company_id=company.id,
        city_id=payload.city_id,
        address_detail=payload.address_detail.strip(),
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, company: Company, address_id: uuid.UUID) -> None:
    address = db.scalar(
        # Lọc kèm company_id: nhà tuyển dụng không xoá được địa chỉ của công ty khác
        # dù có đoán đúng id.
        select(CompanyAddress).where(
            CompanyAddress.id == address_id,
            CompanyAddress.company_id == company.id,
        )
    )
    if address is None:
        raise NotFoundError("ADDRESS_NOT_FOUND", "Không tìm thấy địa chỉ này.")

    db.delete(address)
    db.commit()


def verify_tax_code_matches_name(company_name: str, tax_code: str) -> datetime | None:
    """Đối chiếu tên công ty với dữ liệu VietQR lúc đăng ký.

    Chặn trường hợp người dùng sửa payload để khai tên công ty khác với mã số
    thuế. Trả về thời điểm đối chiếu nếu khớp, None nếu VietQR không phản hồi.

    VietQR chết KHÔNG chặn đăng ký: hồ sơ vẫn được tạo nhưng chưa có dấu đối
    chiếu, admin sẽ soi kỹ hơn khi duyệt.
    """
    try:
        info = vietqr.lookup_tax_code(tax_code)
    except AppError as error:
        if error.code == "TAX_LOOKUP_UNAVAILABLE":
            return None
        raise

    if vietqr.normalize_company_name(info.company_name) != vietqr.normalize_company_name(
        company_name
    ):
        raise AppError(
            "TAX_CODE_NAME_MISMATCH",
            f'Tên công ty không khớp với mã số thuế. Theo đăng ký kinh doanh: "{info.company_name}".',
            status.HTTP_409_CONFLICT,
        )
    return datetime.now(UTC)


# ─────────────────────────── Quản trị viên ───────────────────────────


def list_companies(
    db: Session, *, company_status: CompanyStatus | None, keyword: str | None, page: int, page_size: int
) -> tuple[list[Company], int]:
    stmt = select(Company).where(Company.deleted_at.is_(None))
    stmt = _apply_company_filters(stmt, company_status, keyword)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Company.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(items), total


def count_companies_by_status(db: Session) -> dict[str, int]:
    """Số lượng theo từng trạng thái, để hiện badge trên các tab của admin."""
    rows = db.execute(
        select(Company.status, func.count())
        .where(Company.deleted_at.is_(None))
        .group_by(Company.status)
    ).all()
    counts = {item.value: 0 for item in CompanyStatus}
    for company_status, count in rows:
        counts[company_status.value] = count
    return counts


def get_company_by_id(db: Session, company_id: uuid.UUID) -> Company:
    company = db.scalar(
        select(Company)
        .where(Company.id == company_id, Company.deleted_at.is_(None))
        .options(selectinload(Company.addresses))
    )
    if company is None:
        raise NotFoundError("COMPANY_NOT_FOUND", "Không tìm thấy công ty này.")
    return company


def decide_company(
    db: Session, company: Company, *, new_status: CompanyStatus, rejected_reason: str | None
) -> Company:
    """Duyệt hoặc từ chối hồ sơ công ty."""
    if new_status == CompanyStatus.REJECTED and not (rejected_reason or "").strip():
        raise AppError(
            "REJECTED_REASON_REQUIRED",
            "Vui lòng nhập lý do từ chối để nhà tuyển dụng biết cần sửa gì.",
        )

    company.status = new_status
    company.rejected_reason = rejected_reason.strip() if new_status == CompanyStatus.REJECTED and rejected_reason else None

    if new_status == CompanyStatus.REJECTED:
        # Công ty bị từ chối thì không còn được coi là đã xác thực.
        company.verification_tier = VerificationTier.UNVERIFIED
        # Và mọi tin đang đăng phải biến mất khỏi trang công khai ngay. Gỡ trong
        # cùng transaction với việc đổi trạng thái công ty (DESIGN mục 4.3) —
        # tách ra thì có khoảng thời gian công ty đã bị từ chối mà tin vẫn hiện.
        job_service.take_down_published_jobs(
            db, company, f"Hồ sơ công ty bị từ chối: {company.rejected_reason}"
        )

    db.commit()
    db.refresh(company)
    return company


def set_verification(db: Session, company: Company, tier: VerificationTier) -> Company:
    if tier == VerificationTier.VERIFIED and company.status != CompanyStatus.APPROVED:
        raise AppError(
            "COMPANY_NOT_APPROVED",
            "Chỉ gắn được nhãn đã xác thực cho công ty đã được duyệt.",
        )

    company.verification_tier = tier
    db.commit()
    db.refresh(company)
    return company


def list_users(
    db: Session, *, keyword: str | None, page: int, page_size: int
) -> tuple[list[User], int]:
    stmt = select(User)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(User.full_name.ilike(pattern) | User.email.ilike(pattern))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(items), total


def set_user_active(db: Session, *, admin: User, user_id: uuid.UUID, is_active: bool) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("USER_NOT_FOUND", "Không tìm thấy người dùng này.")

    # Tự khoá tài khoản của mình là mất luôn quyền vào trang quản trị.
    if user.id == admin.id:
        raise AppError(
            "CANNOT_DISABLE_SELF",
            "Bạn không thể khoá chính tài khoản của mình.",
            status.HTTP_403_FORBIDDEN,
        )

    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


# ─────────────────────────── Trang công khai ───────────────────────────


def list_public_companies(
    db: Session, *, keyword: str | None, group_id: uuid.UUID | None, page: int, page_size: int
) -> tuple[list[tuple[Company, int]], int]:
    """Danh sách công ty cho khách, kèm số tin đang tuyển của từng công ty.

    Số tin lấy bằng subquery tương quan ngay trong câu SELECT chính, không lặp
    `db.query` cho từng công ty — 20 công ty một trang mà đếm rời là 20 lượt
    truy vấn thừa (N+1).
    """
    open_job_count = (
        select(func.count(Job.id))
        .where(
            Job.company_id == Company.id,
            Job.status == JobStatus.PUBLISHED,
            Job.deleted_at.is_(None),
            Job.deadline > func.now(),
        )
        .correlate(Company)
        .scalar_subquery()
    )

    stmt = select(Company, open_job_count.label("open_job_count")).where(
        Company.deleted_at.is_(None),
        # Chỉ công ty đã duyệt mới hiện ra ngoài — hồ sơ chờ duyệt hay bị từ
        # chối không phải thứ để khách nhìn thấy.
        Company.status == CompanyStatus.APPROVED,
    )
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(Company.company_name.ilike(pattern) | Company.short_name.ilike(pattern))
    if group_id is not None:
        stmt = stmt.where(Company.category_group_id == group_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        # Công ty đang tuyển nhiều lên trước: người tìm việc vào đây để tìm chỗ
        # nộp hồ sơ, công ty không có tin nào thì đứng đầu cũng vô ích.
        stmt.order_by(open_job_count.desc(), Company.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [(row[0], row[1]) for row in rows], total


def get_public_company_by_slug(db: Session, slug: str) -> Company:
    company = db.scalar(
        select(Company)
        .where(
            Company.slug == slug,
            Company.deleted_at.is_(None),
            Company.status == CompanyStatus.APPROVED,
        )
        .options(selectinload(Company.addresses))
    )
    if company is None:
        raise NotFoundError("COMPANY_NOT_FOUND", "Không tìm thấy công ty này.")
    return company


def _apply_company_filters(
    stmt: Select, company_status: CompanyStatus | None, keyword: str | None
) -> Select:
    if company_status is not None:
        stmt = stmt.where(Company.status == company_status)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(Company.company_name.ilike(pattern) | Company.tax_code.ilike(pattern))
    return stmt
