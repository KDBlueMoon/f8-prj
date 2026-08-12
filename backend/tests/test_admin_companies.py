"""Luồng duyệt công ty và quản lý người dùng của quản trị viên."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header

COMPANIES = "/api/v1/admin/companies"
USERS = "/api/v1/admin/users"


def _decide(client: TestClient, token: str, company_id: str, **payload: object):
    return client.patch(
        f"{COMPANIES}/{company_id}/status", headers=auth_header(token), json=payload
    )


# ─────────────────────────── Phân quyền ───────────────────────────


@pytest.mark.parametrize("path", [COMPANIES, f"{COMPANIES}/counts", USERS])
def test_admin_endpoints_reject_anonymous(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", [COMPANIES, f"{COMPANIES}/counts", USERS])
def test_admin_endpoints_reject_employer(
    client: TestClient, make_employer: Callable[..., dict], path: str
) -> None:
    """Nhà tuyển dụng không được tự duyệt hồ sơ công ty của chính mình."""
    response = client.get(path, headers=auth_header(make_employer()["token"]))

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN_ROLE"


def test_employer_cannot_approve_own_company(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    employer = make_employer()

    response = _decide(client, employer["token"], employer["company_id"], status="APPROVED")

    assert response.status_code == 403


# ─────────────────────────── Duyệt hồ sơ ───────────────────────────


def test_admin_approves_company(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()

    response = _decide(client, admin_token, employer["company_id"], status="APPROVED")

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["rejected_reason"] is None


def test_approval_is_visible_to_the_employer_immediately(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()
    _decide(client, admin_token, employer["company_id"], status="APPROVED")

    response = client.get("/api/v1/employer/company", headers=auth_header(employer["token"]))

    assert response.json()["status"] == "APPROVED"


def test_rejection_requires_a_reason(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    """Từ chối mà không nói lý do thì nhà tuyển dụng không biết phải sửa gì."""
    employer = make_employer()

    response = _decide(client, admin_token, employer["company_id"], status="REJECTED")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "REJECTED_REASON_REQUIRED"


def test_rejection_with_reason_reaches_the_employer(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()

    _decide(
        client,
        admin_token,
        employer["company_id"],
        status="REJECTED",
        rejected_reason="Mã số thuế không khớp tên doanh nghiệp",
    )

    company = client.get(
        "/api/v1/employer/company", headers=auth_header(employer["token"])
    ).json()
    assert company["status"] == "REJECTED"
    assert company["rejected_reason"] == "Mã số thuế không khớp tên doanh nghiệp"


def test_admin_cannot_push_company_back_to_pending(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()

    response = _decide(client, admin_token, employer["company_id"], status="PENDING")

    assert response.status_code == 422


def test_decision_on_unknown_company_returns_404(
    client: TestClient, admin_token: str
) -> None:
    response = _decide(
        client, admin_token, "00000000-0000-0000-0000-000000000000", status="APPROVED"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "COMPANY_NOT_FOUND"


# ─────────────────────────── Nhãn đã xác thực ───────────────────────────


def test_verified_badge_requires_an_approved_company(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    """Không gắn nhãn "đã xác thực" cho hồ sơ còn đang chờ duyệt."""
    employer = make_employer()

    response = client.patch(
        f"{COMPANIES}/{employer['company_id']}/verification",
        headers=auth_header(admin_token),
        json={"verification_tier": "VERIFIED"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "COMPANY_NOT_APPROVED"


def test_admin_can_verify_an_approved_company(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()
    _decide(client, admin_token, employer["company_id"], status="APPROVED")

    response = client.patch(
        f"{COMPANIES}/{employer['company_id']}/verification",
        headers=auth_header(admin_token),
        json={"verification_tier": "VERIFIED"},
    )

    assert response.status_code == 200
    assert response.json()["verification_tier"] == "VERIFIED"


def test_rejecting_a_verified_company_removes_the_badge(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()
    _decide(client, admin_token, employer["company_id"], status="APPROVED")
    client.patch(
        f"{COMPANIES}/{employer['company_id']}/verification",
        headers=auth_header(admin_token),
        json={"verification_tier": "VERIFIED"},
    )

    response = _decide(
        client,
        admin_token,
        employer["company_id"],
        status="REJECTED",
        rejected_reason="Phát hiện thông tin sai lệch",
    )

    assert response.json()["verification_tier"] == "UNVERIFIED"


# ─────────────────────────── Danh sách và lọc ───────────────────────────


def test_pending_filter_shows_the_review_queue(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()

    response = client.get(
        COMPANIES, headers=auth_header(admin_token), params={"status": "PENDING", "page_size": 50}
    )

    assert response.status_code == 200
    assert all(item["status"] == "PENDING" for item in response.json()["items"])
    assert employer["company_id"] in [item["id"] for item in response.json()["items"]]


def test_approved_company_leaves_the_pending_queue(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer()
    _decide(client, admin_token, employer["company_id"], status="APPROVED")

    pending = client.get(
        COMPANIES, headers=auth_header(admin_token), params={"status": "PENDING", "page_size": 50}
    ).json()

    assert employer["company_id"] not in [item["id"] for item in pending["items"]]


def test_search_matches_company_name_and_tax_code(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    employer = make_employer("CÔNG TY CỔ PHẦN TÌM KIẾM ĐỘC NHẤT")

    by_name = client.get(
        COMPANIES, headers=auth_header(admin_token), params={"q": "TÌM KIẾM ĐỘC NHẤT"}
    ).json()
    detail = client.get(
        f"{COMPANIES}/{employer['company_id']}", headers=auth_header(admin_token)
    ).json()
    by_tax_code = client.get(
        COMPANIES, headers=auth_header(admin_token), params={"q": detail["tax_code"]}
    ).json()

    assert [item["id"] for item in by_name["items"]] == [employer["company_id"]]
    assert [item["id"] for item in by_tax_code["items"]] == [employer["company_id"]]


def test_list_response_carries_pagination_metadata(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    make_employer()

    body = client.get(COMPANIES, headers=auth_header(admin_token), params={"page_size": 1}).json()

    assert len(body["items"]) <= 1
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 1
    assert body["meta"]["total"] >= 1
    # Chia lên: còn dư bản ghi là phải có thêm trang.
    assert body["meta"]["total_pages"] == body["meta"]["total"]


def test_counts_endpoint_reflects_decisions(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    before = client.get(f"{COMPANIES}/counts", headers=auth_header(admin_token)).json()
    employer = make_employer()
    after_register = client.get(f"{COMPANIES}/counts", headers=auth_header(admin_token)).json()
    _decide(client, admin_token, employer["company_id"], status="APPROVED")
    after_approve = client.get(f"{COMPANIES}/counts", headers=auth_header(admin_token)).json()

    assert after_register["PENDING"] == before["PENDING"] + 1
    assert after_approve["PENDING"] == before["PENDING"]
    assert after_approve["APPROVED"] == before["APPROVED"] + 1


def test_counts_route_is_not_swallowed_by_the_id_route(
    client: TestClient, admin_token: str
) -> None:
    """/companies/counts phải khớp trước /companies/{company_id}."""
    response = client.get(f"{COMPANIES}/counts", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert "PENDING" in response.json()


# ─────────────────────────── Quản lý người dùng ───────────────────────────


def test_admin_can_disable_a_user_and_block_their_access(
    client: TestClient, make_candidate: Callable[[], str], admin_token: str
) -> None:
    token = make_candidate()
    user_id = client.get("/api/v1/auth/me", headers=auth_header(token)).json()["user"]["id"]

    response = client.patch(
        f"{USERS}/{user_id}/status", headers=auth_header(admin_token), json={"is_active": False}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    # Khoá xong là chặn được ngay, không chờ access token hết hạn.
    assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 403


def test_admin_cannot_disable_their_own_account(
    client: TestClient, admin_token: str
) -> None:
    """Tự khoá mình là mất luôn quyền vào trang quản trị."""
    me = client.get("/api/v1/auth/me", headers=auth_header(admin_token)).json()

    response = client.patch(
        f"{USERS}/{me['user']['id']}/status",
        headers=auth_header(admin_token),
        json={"is_active": False},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "CANNOT_DISABLE_SELF"


def test_user_list_never_exposes_password_hash(
    client: TestClient, make_candidate: Callable[[], str], admin_token: str
) -> None:
    make_candidate()

    response = client.get(USERS, headers=auth_header(admin_token))

    assert response.status_code == 200
    assert "password" not in response.text
