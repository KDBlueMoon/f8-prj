"""Nghiệp vụ đăng ký, đăng nhập và vòng đời refresh token."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.core.errors import AppError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.auth import RefreshToken
from app.db.models.company import Company, CompanyMember
from app.db.models.enums import CompanyStatus, MemberRole, UserRole
from app.db.models.user import User
from app.schemas.auth import CompanyRegistrationInfo
from app.utils.slug import unique_slug

_SLUG_SUFFIX_LENGTH = 6

# Dùng chung cho mọi trường hợp đăng nhập thất bại: sai email, sai mật khẩu hay
# email không tồn tại đều trả một thông báo, để không lộ email nào đã đăng ký.
_INVALID_CREDENTIALS = AppError(
    "INVALID_CREDENTIALS",
    "Email hoặc mật khẩu không đúng.",
    status.HTTP_401_UNAUTHORIZED,
)

# Hash thật của một mật khẩu vô nghĩa, dùng để so khi email không tồn tại.
# Nhờ vậy thời gian phản hồi của "email không tồn tại" và "sai mật khẩu" tương
# đương nhau, kẻ tấn công không dò được email nào đã đăng ký qua thời gian đáp.
_DUMMY_PASSWORD_HASH = hash_password("khong-phai-mat-khau-that-0")


def _company_slug(company_name: str, company_id: uuid.UUID) -> str:
    return unique_slug(company_name, suffix=company_id.hex[:_SLUG_SUFFIX_LENGTH])


def register_candidate(
    db: Session, *, email: str, password: str, full_name: str, phone_number: str | None
) -> User:
    _ensure_email_available(db, email)

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.CANDIDATE,
        full_name=full_name.strip(),
        phone_number=phone_number,
    )
    db.add(user)
    _commit(db, on_integrity_error=_email_or_tax_conflict)
    return user


def register_employer(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    phone_number: str | None,
    company_info: CompanyRegistrationInfo,
) -> tuple[User, Company]:
    """Tạo user, công ty (trạng thái PENDING) và liên kết OWNER trong một giao dịch.

    Tất cả cùng thành công hoặc cùng thất bại — tránh sinh ra user nhà tuyển
    dụng mồ côi không gắn với công ty nào.
    """
    _ensure_email_available(db, email)
    _ensure_tax_code_available(db, company_info.tax_code)

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.EMPLOYER,
        full_name=full_name.strip(),
        phone_number=phone_number,
    )
    # Gán id ngay ở tầng Python: cần user.id và company.id để tạo liên kết
    # CompanyMember và sinh slug, trong khi slug là NOT NULL nên không thể
    # flush trước rồi mới điền.
    user.id = uuid.uuid4()
    db.add(user)

    company = Company(
        tax_code=company_info.tax_code,
        company_name=company_info.company_name.strip(),
        international_name=company_info.international_name,
        short_name=company_info.short_name,
        director=company_info.director.strip(),
        headquarters_address=company_info.headquarters_address.strip(),
        issued_date=company_info.issued_date,
        email=company_info.email,
        phone_number=company_info.phone_number,
        website=company_info.website,
        company_size=company_info.company_size,
        category_group_id=company_info.category_group_id,
        status=CompanyStatus.PENDING,
    )
    company.id = uuid.uuid4()
    company.slug = _company_slug(company.company_name, company.id)
    db.add(company)

    db.add(
        CompanyMember(
            user_id=user.id, company_id=company.id, member_role=MemberRole.OWNER
        )
    )
    _commit(db, on_integrity_error=_email_or_tax_conflict)
    return user, company


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        raise _INVALID_CREDENTIALS

    if not verify_password(password, user.password_hash):
        raise _INVALID_CREDENTIALS

    if not user.is_active:
        raise AppError(
            "ACCOUNT_DISABLED",
            "Tài khoản đã bị khoá. Vui lòng liên hệ quản trị viên.",
            status.HTTP_403_FORBIDDEN,
        )
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    """Phát hành cặp access + refresh token và ghi nhận refresh token vào DB."""
    access_token = create_access_token(user.id, user.role.value)
    refresh_token, jti, expires_at = create_refresh_token(user.id)

    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
    db.commit()
    return access_token, refresh_token


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str, str]:
    """Đổi refresh token cũ lấy cặp token mới, đồng thời thu hồi token cũ.

    Luân chuyển mỗi lần làm mới: token đã dùng lập tức vô hiệu, nên bản sao bị
    đánh cắp chỉ dùng được đúng một lần trước khi hỏng.
    """
    payload = decode_token(raw_token, expected_type="refresh")
    if payload is None:
        raise invalid_refresh_token()

    stored = db.scalar(select(RefreshToken).where(RefreshToken.jti == payload.get("jti")))
    if stored is None or stored.revoked_at is not None:
        raise invalid_refresh_token()
    if stored.expires_at <= datetime.now(UTC):
        raise invalid_refresh_token()

    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise invalid_refresh_token()

    stored.revoked_at = datetime.now(UTC)
    access_token, refresh_token = issue_tokens(db, user)
    return user, access_token, refresh_token


def revoke_refresh_token(db: Session, raw_token: str | None) -> None:
    """Thu hồi token khi logout. Token không hợp lệ thì bỏ qua im lặng.

    Logout luôn phải thành công dưới góc nhìn người dùng — báo lỗi ở bước này
    chỉ khiến họ mắc kẹt ở trạng thái đã đăng nhập.
    """
    if not raw_token:
        return

    payload = decode_token(raw_token, expected_type="refresh")
    if payload is None:
        return

    db.execute(
        update(RefreshToken)
        .where(RefreshToken.jti == payload.get("jti"), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()


def get_company_for_user(db: Session, user: User) -> Company | None:
    if user.role != UserRole.EMPLOYER:
        return None
    return db.scalar(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(CompanyMember.user_id == user.id)
    )


def invalid_refresh_token() -> AppError:
    return AppError(
        "INVALID_REFRESH_TOKEN",
        "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
        status.HTTP_401_UNAUTHORIZED,
    )


def _ensure_email_available(db: Session, email: str) -> None:
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise ConflictError("EMAIL_TAKEN", "Email này đã được đăng ký.")


def _ensure_tax_code_available(db: Session, tax_code: str) -> None:
    if db.scalar(select(Company.id).where(Company.tax_code == tax_code)) is not None:
        raise ConflictError("TAX_CODE_TAKEN", "Mã số thuế này đã có công ty đăng ký.")


def _email_or_tax_conflict(error: IntegrityError) -> AppError:
    """Chuyển lỗi ràng buộc UNIQUE của DB thành lỗi nghiệp vụ dễ hiểu.

    Kiểm tra trùng ở trên vẫn có khe hở khi hai request vào cùng lúc; ràng buộc
    UNIQUE mới là chốt chặn thật, nên phải dịch được lỗi của nó.
    """
    message = str(error.orig)
    if "tax_code" in message:
        return ConflictError("TAX_CODE_TAKEN", "Mã số thuế này đã có công ty đăng ký.")
    if "email" in message:
        return ConflictError("EMAIL_TAKEN", "Email này đã được đăng ký.")
    return ConflictError("DUPLICATE_RECORD", "Dữ liệu đã tồn tại trên hệ thống.")


def _commit(db: Session, *, on_integrity_error: Callable[[IntegrityError], AppError]) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise on_integrity_error(error) from error
