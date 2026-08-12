"""Fixture dùng chung cho test.

Test chạy trên chính database dev. Mỗi test tạo dữ liệu với email/mã số thuế
sinh ngẫu nhiên rồi tự dọn ở cuối, nên không đụng vào dữ liệu sẵn có và chạy
lại nhiều lần vẫn cho kết quả như nhau.
"""

import uuid
from collections.abc import Callable, Generator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.auth import RefreshToken
from app.db.models.company import Company, CompanyMember
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import app

PASSWORD = "MatKhau123"


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def isolate_client_state(client: TestClient) -> None:
    """Đưa bộ đếm rate limit và cookie về trạng thái sạch trước mỗi test.

    TestClient giữ cookie giữa các request, còn limiter đếm theo IP — không dọn
    thì test này ảnh hưởng test kia và kết quả phụ thuộc thứ tự chạy.
    """
    app.state.limiter.reset()
    client.cookies.clear()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def unique_email() -> Callable[[], str]:
    def make() -> str:
        return f"test-{uuid.uuid4().hex[:12]}@example.com"

    return make


@pytest.fixture
def unique_tax_code() -> Callable[[], str]:
    def make() -> str:
        # 10 chữ số, sinh từ uuid để hai lần chạy không đụng nhau.
        return str(uuid.uuid4().int)[:10]

    return make


@pytest.fixture
def cleanup_users(db: Session) -> Iterator[list[str]]:
    """Ghi nhận email đã tạo trong test và xoá sạch user/company liên quan sau đó."""
    emails: list[str] = []
    yield emails

    if not emails:
        return

    user_ids = list(db.scalars(select(User.id).where(User.email.in_(emails))).all())
    if user_ids:
        company_ids = list(
            db.scalars(
                select(CompanyMember.company_id).where(CompanyMember.user_id.in_(user_ids))
            ).all()
        )
        db.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(user_ids)))
        db.execute(delete(CompanyMember).where(CompanyMember.user_id.in_(user_ids)))
        db.execute(delete(User).where(User.id.in_(user_ids)))
        if company_ids:
            db.execute(delete(Company).where(Company.id.in_(company_ids)))
        db.commit()
