"""Fixture dùng chung cho test.

Test chạy trên chính database dev. Mỗi test tạo dữ liệu với email/mã số thuế
sinh ngẫu nhiên rồi tự dọn ở cuối, nên không đụng vào dữ liệu sẵn có và chạy
lại nhiều lần vẫn cho kết quả như nhau.
"""

import uuid
from collections.abc import Callable, Generator, Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.auth import RefreshToken
from app.db.models.company import Company, CompanyMember
from app.db.models.user import User
from app.db.session import SessionLocal
from app.integrations import vietqr
from app.main import app

PASSWORD = "MatKhau123"

VIETQR_ROUTE = "vietqr_business"


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


@pytest.fixture(autouse=True)
def vietqr_mock() -> Generator[respx.MockRouter, None, None]:
    """Chặn mọi lượt gọi VietQR trong test — test không được đụng mạng ngoài.

    Mặc định giả lập VietQR không phản hồi, vì đó là trường hợp KHÔNG chặn đăng
    ký: hồ sơ vẫn tạo được nhưng chưa có dấu đối chiếu mã số thuế. Test nào cần
    kịch bản khác thì tự đổi route qua `vietqr_mock[VIETQR_ROUTE].mock(...)`.
    """
    # Cache nằm trong bộ nhớ tiến trình, không xoá thì kết quả của test này rơi
    # sang test kia.
    vietqr.clear_cache()

    with respx.mock(base_url=settings.VIETQR_BASE_URL, assert_all_called=False) as router:
        router.get(path__regex=r"/business/\d+", name=VIETQR_ROUTE).mock(
            side_effect=httpx.ConnectTimeout("VietQR bị chặn trong test")
        )
        yield router

    vietqr.clear_cache()


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


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_candidate(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> Callable[[], str]:
    """Tạo ứng viên mới và trả về access token."""

    def make() -> str:
        email = unique_email()
        cleanup_users.append(email)
        response = client.post(
            "/api/v1/auth/register/candidate",
            json={"email": email, "password": PASSWORD, "full_name": "Ứng viên Test"},
        )
        return response.json()["access_token"]

    return make


@pytest.fixture
def make_employer(
    client: TestClient,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
) -> Callable[..., dict]:
    """Tạo nhà tuyển dụng kèm công ty (PENDING) và trả về token + thông tin công ty."""

    def make(company_name: str = "CÔNG TY TNHH KIỂM THỬ") -> dict:
        email = unique_email()
        cleanup_users.append(email)
        response = client.post(
            "/api/v1/auth/register/employer",
            json={
                "email": email,
                "password": PASSWORD,
                "full_name": "Nhà tuyển dụng Test",
                "company": {
                    "tax_code": unique_tax_code(),
                    "company_name": company_name,
                    "director": "Nguyễn Kiểm Thử",
                    "headquarters_address": "1 Đường Thử Nghiệm, Hà Nội",
                    "email": "hr@kiemthu.vn",
                    "phone_number": "0901234567",
                    "company_size": "10-24",
                },
            },
        )
        body = response.json()
        return {
            "email": email,
            "token": body["access_token"],
            "company_id": body["company"]["id"],
        }

    return make


@pytest.fixture
def admin_token(
    client: TestClient, db: Session, unique_email: Callable[[], str], cleanup_users: list[str]
) -> str:
    """Tài khoản ADMIN tạo thẳng trong DB — không có endpoint đăng ký admin."""
    from app.core.security import hash_password
    from app.db.models.enums import UserRole

    email = unique_email()
    cleanup_users.append(email)
    db.add(
        User(
            email=email,
            password_hash=hash_password(PASSWORD),
            role=UserRole.ADMIN,
            full_name="Quản trị viên Test",
        )
    )
    db.commit()

    response = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return response.json()["access_token"]


@pytest.fixture
def make_approved_employer(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> Callable[..., dict]:
    """Nhà tuyển dụng đã được admin duyệt — điều kiện cần để đăng tin."""

    def make(company_name: str = "CÔNG TY TNHH ĐÃ DUYỆT") -> dict:
        employer = make_employer(company_name)
        client.patch(
            f"/api/v1/admin/companies/{employer['company_id']}/status",
            headers=auth_header(admin_token),
            json={"status": "APPROVED"},
        )
        return employer

    return make


@pytest.fixture
def any_category_id(client: TestClient) -> str:
    """Id một ngành nghề có thật, lấy từ dữ liệu seed."""
    groups = client.get("/api/v1/categories").json()
    return groups[0]["categories"][0]["id"]


@pytest.fixture
def job_payload(any_category_id: str) -> Callable[..., dict]:
    """Payload tạo tin hợp lệ; truyền keyword để ghi đè từng trường."""

    def make(**overrides: object) -> dict:
        payload = {
            "title": "Lập trình viên Backend Python",
            "category_id": any_category_id,
            "job_type": "FULL_TIME",
            "experience_level": "1_2",
            "quantity": 2,
            "salary_type": "RANGE",
            "salary_min": 20_000_000,
            "salary_max": 35_000_000,
            "deadline": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
            "description_html": "<p>Mô tả công việc</p>",
            "requirements_html": "<p>Yêu cầu ứng viên</p>",
            "benefits_html": "<p>Quyền lợi</p>",
            "locations": [{"city_id": 1, "address_detail": "47 Nguyễn Tuân"}],
        }
        payload.update(overrides)
        return payload

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
