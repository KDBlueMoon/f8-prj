import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.models.enums import CompanySize, CompanyStatus, MemberRole, VerificationTier


def _enum(py_enum, name: str) -> Enum:
    """PG enum lưu theo .value của Python enum (không phải tên biến)."""
    return Enum(py_enum, name=name, values_callable=lambda e: [i.value for i in e])


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"

    # Mã số thuế là khoá nghiệp vụ: 1 MST = 1 công ty trên hệ thống.
    tax_code: Mapped[str] = mapped_column(String(14), nullable=False, unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    international_name: Mapped[str | None] = mapped_column(String(500))
    short_name: Mapped[str | None] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # VietQR không trả 2 trường này — nhà tuyển dụng tự nhập.
    director: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)

    headquarters_address: Mapped[str] = mapped_column(Text, nullable=False)
    issued_date: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    company_size: Mapped[CompanySize] = mapped_column(
        _enum(CompanySize, "company_size"), nullable=False
    )
    category_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category_groups.id", ondelete="SET NULL")
    )
    description_html: Mapped[str | None] = mapped_column(Text)

    status: Mapped[CompanyStatus] = mapped_column(
        _enum(CompanyStatus, "company_status"),
        nullable=False,
        default=CompanyStatus.PENDING,
        index=True,
    )
    rejected_reason: Mapped[str | None] = mapped_column(Text)
    verification_tier: Mapped[VerificationTier] = mapped_column(
        _enum(VerificationTier, "verification_tier"),
        nullable=False,
        default=VerificationTier.UNVERIFIED,
    )
    # Thời điểm tên công ty được đối chiếu khớp với VietQR. NULL nghĩa là chưa
    # đối chiếu được (VietQR không phản hồi lúc đăng ký) — admin cần soi kỹ hơn
    # khi duyệt hồ sơ này.
    tax_code_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Soft delete: giữ lịch sử ứng tuyển của ứng viên khi công ty bị xoá.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    addresses: Mapped[list["CompanyAddress"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    members: Mapped[list["CompanyMember"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class CompanyMember(Base, UUIDMixin, TimestampMixin):
    """Liên kết user EMPLOYER với công ty. Mỗi user thuộc đúng 1 công ty."""

    __tablename__ = "company_members"
    __table_args__ = (UniqueConstraint("user_id", name="uq_company_members_user"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    member_role: Mapped[MemberRole] = mapped_column(
        _enum(MemberRole, "member_role"), nullable=False, default=MemberRole.RECRUITER
    )

    company: Mapped["Company"] = relationship(back_populates="members")


class CompanyAddress(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "company_addresses"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False
    )
    address_detail: Mapped[str] = mapped_column(Text, nullable=False)

    company: Mapped["Company"] = relationship(back_populates="addresses")
