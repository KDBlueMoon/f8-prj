from datetime import date
from typing import Self

from sqlalchemy import Date, Enum, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base, session
from models import ActiveRecordMixin, TimestampMixin, UUIDMixin
from models.enums import CompanyStatus, VerificationTier


class Company(Base, UUIDMixin, TimestampMixin, ActiveRecordMixin):
    __tablename__ = "companies"

    tax_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    international_name: Mapped[str | None] = mapped_column(String(255))
    short_name: Mapped[str | None] = mapped_column(String(255))
    director: Mapped[str | None] = mapped_column(String(255))
    headquarters_address: Mapped[str | None] = mapped_column(String(500))
    issued_date: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    company_size: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(255))
    description_html: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, name="company_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=CompanyStatus.PENDING,
    )
    verification_tier: Mapped[VerificationTier] = mapped_column(
        Enum(
            VerificationTier,
            name="verification_tier",
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=VerificationTier.UNVERIFIED,
    )

    @classmethod
    def search(cls, *, keyword: str | None = None, limit: int, offset: int) -> tuple[list[Self], int]:
        stmt = select(cls)
        if keyword:
            stmt = stmt.where(cls.company_name.ilike(f"%{keyword}%"))

        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(cls.created_at.desc()).offset(offset).limit(limit)
        items = list(session.scalars(stmt).all())
        return items, total
