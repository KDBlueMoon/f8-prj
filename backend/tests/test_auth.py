from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.auth import RefreshToken
from app.db.models.company import Company
from app.db.models.enums import CompanyStatus, UserRole, VerificationTier
from app.db.models.user import User
from tests.conftest import PASSWORD

REGISTER_CANDIDATE = "/api/v1/auth/register/candidate"
REGISTER_EMPLOYER = "/api/v1/auth/register/employer"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"


def _candidate_payload(email: str) -> dict:
    return {
        "email": email,
        "password": PASSWORD,
        "full_name": "Nguyễn Văn A",
        "phone_number": "0901234567",
    }


def _employer_payload(email: str, tax_code: str) -> dict:
    return {
        "email": email,
        "password": PASSWORD,
        "full_name": "Trần Thị B",
        "phone_number": "0912345678",
        "company": {
            "tax_code": tax_code,
            "company_name": "CÔNG TY CỔ PHẦN CÔNG NGHỆ ĐẦU TƯ",
            "international_name": "INVESTMENT TECHNOLOGY JSC",
            "short_name": "INVESTTECH",
            "director": "Trần Thị B",
            "headquarters_address": "47 Nguyễn Tuân, Thanh Xuân, Hà Nội",
            "email": "hr@investtech.vn",
            "phone_number": "02466805588",
            "company_size": "100-499",
        },
    }


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────── Đăng ký ứng viên ───────────────────────────


def test_register_candidate_returns_token_and_sets_refresh_cookie(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)

    response = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["role"] == UserRole.CANDIDATE.value
    assert body["company"] is None
    assert settings.REFRESH_COOKIE_NAME in response.cookies


def test_register_never_returns_password_hash(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)

    response = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    assert "password" not in response.text
    assert "hash" not in response.text


def test_register_duplicate_email_returns_conflict(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    response = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EMAIL_TAKEN"


def test_register_email_is_case_insensitive(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    """Cột email dùng CITEXT nên "A@x.com" và "a@x.com" phải coi là một."""
    email = unique_email()
    cleanup_users.append(email)
    client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    response = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email.upper()))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EMAIL_TAKEN"


@pytest.mark.parametrize(
    "password",
    ["short1", "khongcochuso", "12345678", "       1a"],
    ids=["qua-ngan", "thieu-so", "thieu-chu", "khoang-trang"],
)
def test_register_rejects_weak_password(
    client: TestClient, unique_email: Callable[[], str], password: str
) -> None:
    payload = _candidate_payload(unique_email()) | {"password": password}

    response = client.post(REGISTER_CANDIDATE, json=payload)

    assert response.status_code == 422


def test_register_accepts_long_vietnamese_password(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    """Mật khẩu tiếng Việt dài quá 72 byte vẫn phải đăng ký và đăng nhập được.

    bcrypt chỉ nhận 72 byte; ký tự tiếng Việt tốn 3 byte nên nếu không băm
    trước sẽ lỗi hoặc bị cắt cụt âm thầm.
    """
    email = unique_email()
    cleanup_users.append(email)
    long_password = "Mật khẩu rất dài của người dùng Việt Nam 2026" * 2

    register = client.post(
        REGISTER_CANDIDATE, json=_candidate_payload(email) | {"password": long_password}
    )
    assert register.status_code == 201

    login = client.post(LOGIN, json={"email": email, "password": long_password})
    assert login.status_code == 200


@pytest.mark.parametrize(
    "phone", ["123", "0901234", "+84901234567", "abcdefghij"], ids=["ngan", "thieu-so", "co-+84", "chu"]
)
def test_register_rejects_invalid_phone(
    client: TestClient, unique_email: Callable[[], str], phone: str
) -> None:
    payload = _candidate_payload(unique_email()) | {"phone_number": phone}

    response = client.post(REGISTER_CANDIDATE, json=payload)

    assert response.status_code == 422


# ────────────────────── Đăng ký nhà tuyển dụng ──────────────────────


def test_register_employer_creates_pending_company(
    client: TestClient,
    db: Session,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
) -> None:
    email = unique_email()
    cleanup_users.append(email)

    response = client.post(REGISTER_EMPLOYER, json=_employer_payload(email, unique_tax_code()))

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == UserRole.EMPLOYER.value
    company = body["company"]
    # Chưa được duyệt thì chưa đăng tin được (chặn ở P3).
    assert company["status"] == CompanyStatus.PENDING.value
    assert company["verification_tier"] == VerificationTier.UNVERIFIED.value
    assert company["slug"].startswith("cong-ty-co-phan-cong-nghe-dau-tu-")

    stored = db.scalar(select(Company).where(Company.id == company["id"]))
    assert stored is not None
    assert stored.director == "Trần Thị B"


def test_register_employer_rejects_duplicate_tax_code(
    client: TestClient,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
) -> None:
    tax_code = unique_tax_code()
    first_email, second_email = unique_email(), unique_email()
    cleanup_users.extend([first_email, second_email])
    client.post(REGISTER_EMPLOYER, json=_employer_payload(first_email, tax_code))

    response = client.post(REGISTER_EMPLOYER, json=_employer_payload(second_email, tax_code))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "TAX_CODE_TAKEN"


@pytest.mark.parametrize("tax_code", ["123", "abcdefghij", "12345678901"], ids=["ngan", "chu", "11-so"])
def test_register_employer_rejects_invalid_tax_code(
    client: TestClient, unique_email: Callable[[], str], tax_code: str
) -> None:
    response = client.post(REGISTER_EMPLOYER, json=_employer_payload(unique_email(), tax_code))

    assert response.status_code == 422


def test_failed_employer_registration_leaves_no_orphan_user(
    client: TestClient,
    db: Session,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
) -> None:
    """Mã số thuế trùng thì không được để lại user nhà tuyển dụng mồ côi."""
    tax_code = unique_tax_code()
    first_email, second_email = unique_email(), unique_email()
    cleanup_users.append(first_email)
    client.post(REGISTER_EMPLOYER, json=_employer_payload(first_email, tax_code))

    client.post(REGISTER_EMPLOYER, json=_employer_payload(second_email, tax_code))

    assert db.scalar(select(User).where(User.email == second_email)) is None


# ─────────────────────────── Đăng nhập ───────────────────────────


def test_login_succeeds_with_correct_credentials(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    response = client.post(LOGIN, json={"email": email, "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_does_not_reveal_whether_email_exists(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    """Sai mật khẩu và email không tồn tại phải trả cùng một phản hồi."""
    email = unique_email()
    cleanup_users.append(email)
    client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    wrong_password = client.post(LOGIN, json={"email": email, "password": "SaiMatKhau9"})
    unknown_email = client.post(LOGIN, json={"email": unique_email(), "password": PASSWORD})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_login_blocked_for_disabled_account(
    client: TestClient, db: Session, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    user.is_active = False
    db.commit()

    response = client.post(LOGIN, json={"email": email, "password": PASSWORD})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ACCOUNT_DISABLED"


def test_login_rate_limited_after_repeated_attempts(
    client: TestClient, unique_email: Callable[[], str]
) -> None:
    """Chặn dò mật khẩu: quá 5 lần/phút từ cùng IP thì trả 429."""
    email = unique_email()
    payload = {"email": email, "password": "SaiMatKhau9"}

    statuses = [client.post(LOGIN, json=payload).status_code for _ in range(7)]

    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


# ────────────────────────── /auth/me và RBAC ──────────────────────────


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get(ME)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "NOT_AUTHENTICATED"


def test_me_rejects_malformed_token(client: TestClient) -> None:
    response = client.get(ME, headers=_auth_header("khong-phai-jwt"))

    assert response.status_code == 401


def test_me_rejects_refresh_token_used_as_access_token(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    """Refresh token không được dùng thay access token."""
    email = unique_email()
    cleanup_users.append(email)
    register = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))
    refresh_token = register.cookies[settings.REFRESH_COOKIE_NAME]

    response = client.get(ME, headers=_auth_header(refresh_token))

    assert response.status_code == 401


def test_me_returns_company_for_employer(
    client: TestClient,
    unique_email: Callable[[], str],
    unique_tax_code: Callable[[], str],
    cleanup_users: list[str],
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    register = client.post(REGISTER_EMPLOYER, json=_employer_payload(email, unique_tax_code()))
    token = register.json()["access_token"]

    response = client.get(ME, headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json()["company"]["status"] == CompanyStatus.PENDING.value


def test_me_has_no_company_for_candidate(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    token = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email)).json()["access_token"]

    response = client.get(ME, headers=_auth_header(token))

    assert response.json()["company"] is None


def test_disabled_account_loses_access_immediately(
    client: TestClient, db: Session, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    """Khoá tài khoản phải chặn được ngay, không chờ access token hết hạn."""
    email = unique_email()
    cleanup_users.append(email)
    token = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email)).json()["access_token"]
    assert client.get(ME, headers=_auth_header(token)).status_code == 200

    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    user.is_active = False
    db.commit()

    assert client.get(ME, headers=_auth_header(token)).status_code == 403


# ──────────────────────── Refresh và logout ────────────────────────


def test_refresh_issues_new_access_token(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))

    response = client.post(REFRESH)

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_refresh_without_cookie_is_rejected(client: TestClient) -> None:
    response = client.post(REFRESH)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"


def test_refresh_rotates_and_invalidates_old_token(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    """Token cũ phải chết ngay sau khi luân chuyển, để bản sao bị đánh cắp chỉ
    dùng được đúng một lần."""
    email = unique_email()
    cleanup_users.append(email)
    register = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))
    old_refresh = register.cookies[settings.REFRESH_COOKIE_NAME]

    assert client.post(REFRESH).status_code == 200

    client.cookies.clear()
    client.cookies.set(settings.REFRESH_COOKIE_NAME, old_refresh, path="/api/v1/auth")
    replay = client.post(REFRESH)

    assert replay.status_code == 401
    assert replay.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"


def test_logout_revokes_refresh_token_in_database(
    client: TestClient, db: Session, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None

    assert client.post(LOGOUT).status_code == 204

    tokens = db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id)).all()
    assert tokens
    assert all(token.revoked_at is not None for token in tokens)


def test_refresh_fails_after_logout(
    client: TestClient, unique_email: Callable[[], str], cleanup_users: list[str]
) -> None:
    email = unique_email()
    cleanup_users.append(email)
    register = client.post(REGISTER_CANDIDATE, json=_candidate_payload(email))
    refresh_token = register.cookies[settings.REFRESH_COOKIE_NAME]
    client.post(LOGOUT)

    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_token, path="/api/v1/auth")
    response = client.post(REFRESH)

    assert response.status_code == 401


def test_logout_succeeds_without_session(client: TestClient) -> None:
    """Logout khi chưa đăng nhập vẫn phải thành công, không báo lỗi."""
    assert client.post(LOGOUT).status_code == 204
