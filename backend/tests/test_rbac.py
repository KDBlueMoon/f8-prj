"""Kiểm tra dependency phân quyền — chốt chặn thật của hệ thống.

Dùng app phụ với vài route tối giản để test riêng dependency, không phụ thuộc
vào endpoint nghiệp vụ nào (các endpoint đó tới P2/P3 mới có).
"""

from collections.abc import Callable, Generator

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.deps import require_admin, require_candidate, require_employer
from app.core.errors import AppError
from app.db.models.user import User
from tests.conftest import PASSWORD

REGISTER_CANDIDATE = "/api/v1/auth/register/candidate"
REGISTER_EMPLOYER = "/api/v1/auth/register/employer"


@pytest.fixture(scope="module")
def rbac_client() -> Generator[TestClient, None, None]:
    guarded = FastAPI()

    @guarded.exception_handler(AppError)
    def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"code": exc.code, "message": exc.message}},
        )

    @guarded.get("/only-candidate")
    def only_candidate(user: User = Depends(require_candidate)) -> dict[str, str]:
        return {"role": user.role.value}

    @guarded.get("/only-employer")
    def only_employer(user: User = Depends(require_employer)) -> dict[str, str]:
        return {"role": user.role.value}

    @guarded.get("/only-admin")
    def only_admin(user: User = Depends(require_admin)) -> dict[str, str]:
        return {"role": user.role.value}

    with TestClient(guarded) as test_client:
        yield test_client


@pytest.fixture
def candidate_token(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> str:
    email = unique_email()
    cleanup_users.append(email)
    response = client.post(
        REGISTER_CANDIDATE,
        json={"email": email, "password": PASSWORD, "full_name": "Ứng viên Test"},
    )
    return response.json()["access_token"]


@pytest.fixture
def employer_token(
    client: TestClient,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
) -> str:
    email = unique_email()
    cleanup_users.append(email)
    response = client.post(
        REGISTER_EMPLOYER,
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": "Nhà tuyển dụng Test",
            "company": {
                "tax_code": unique_tax_code(),
                "company_name": "CÔNG TY TNHH KIỂM THỬ",
                "director": "Nguyễn Kiểm Thử",
                "headquarters_address": "1 Đường Thử Nghiệm, Hà Nội",
                "email": "hr@kiemthu.vn",
                "phone_number": "0901234567",
                "company_size": "10-24",
            },
        },
    )
    return response.json()["access_token"]


def _header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("path", ["/only-candidate", "/only-employer", "/only-admin"])
def test_guarded_routes_reject_anonymous_request(rbac_client: TestClient, path: str) -> None:
    response = rbac_client.get(path)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "NOT_AUTHENTICATED"


def test_candidate_can_access_candidate_route(rbac_client: TestClient, candidate_token: str) -> None:
    response = rbac_client.get("/only-candidate", headers=_header(candidate_token))

    assert response.status_code == 200
    assert response.json()["role"] == "CANDIDATE"


@pytest.mark.parametrize("path", ["/only-employer", "/only-admin"])
def test_candidate_blocked_from_other_roles(
    rbac_client: TestClient, candidate_token: str, path: str
) -> None:
    response = rbac_client.get(path, headers=_header(candidate_token))

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN_ROLE"


def test_employer_can_access_employer_route(rbac_client: TestClient, employer_token: str) -> None:
    response = rbac_client.get("/only-employer", headers=_header(employer_token))

    assert response.status_code == 200
    assert response.json()["role"] == "EMPLOYER"


@pytest.mark.parametrize("path", ["/only-candidate", "/only-admin"])
def test_employer_blocked_from_other_roles(
    rbac_client: TestClient, employer_token: str, path: str
) -> None:
    """Quan trọng: nhà tuyển dụng không được ứng tuyển (chặn từ P5)."""
    response = rbac_client.get(path, headers=_header(employer_token))

    assert response.status_code == 403
