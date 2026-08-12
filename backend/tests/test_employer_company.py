"""Hồ sơ công ty của nhà tuyển dụng, tập trung vào ranh giới giữa các công ty."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from tests.conftest import auth_header

COMPANY = "/api/v1/employer/company"
ADDRESSES = "/api/v1/employer/company/addresses"


def test_employer_sees_own_company(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    employer = make_employer("CÔNG TY TNHH ALPHA")

    response = client.get(COMPANY, headers=auth_header(employer["token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == "CÔNG TY TNHH ALPHA"
    assert body["status"] == "PENDING"
    assert body["addresses"] == []


def test_company_endpoint_takes_no_id_so_employers_cannot_reach_each_other(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    """Công ty được suy ra từ token, không nhận id từ client.

    Đây là cách chặn IDOR: không có tham số nào để đổi thành id công ty khác.
    """
    alpha = make_employer("CÔNG TY TNHH ALPHA")
    beta = make_employer("CÔNG TY TNHH BETA")

    alpha_view = client.get(COMPANY, headers=auth_header(alpha["token"])).json()
    beta_view = client.get(COMPANY, headers=auth_header(beta["token"])).json()

    assert alpha_view["id"] == alpha["company_id"]
    assert beta_view["id"] == beta["company_id"]
    assert alpha_view["id"] != beta_view["id"]


def test_candidate_cannot_access_employer_company(
    client: TestClient, make_candidate: Callable[[], str]
) -> None:
    response = client.get(COMPANY, headers=auth_header(make_candidate()))

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN_ROLE"


def test_anonymous_cannot_access_employer_company(client: TestClient) -> None:
    assert client.get(COMPANY).status_code == 401


def test_employer_can_update_own_profile(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    employer = make_employer()

    response = client.patch(
        COMPANY,
        headers=auth_header(employer["token"]),
        json={"director": "Người Đại Diện Mới", "company_size": "100-499"},
    )

    assert response.status_code == 200
    assert response.json()["director"] == "Người Đại Diện Mới"
    assert response.json()["company_size"] == "100-499"


def test_update_ignores_tax_code_because_it_is_not_editable(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    """Mã số thuế là khoá đã dùng để đối chiếu VietQR.

    Cho sửa thì có thể đăng ký bằng một mã hợp lệ rồi đổi sang mã khác sau khi
    được duyệt.
    """
    employer = make_employer()
    original = client.get(COMPANY, headers=auth_header(employer["token"])).json()["tax_code"]

    response = client.patch(
        COMPANY, headers=auth_header(employer["token"]), json={"tax_code": "9999999999"}
    )

    assert response.status_code == 200
    assert response.json()["tax_code"] == original


def test_editing_a_rejected_profile_puts_it_back_in_the_review_queue(
    client: TestClient, make_employer: Callable[..., dict], admin_token: str
) -> None:
    """Không có bước này thì hồ sơ bị từ chối sẽ mắc kẹt vĩnh viễn."""
    employer = make_employer()
    client.patch(
        f"/api/v1/admin/companies/{employer['company_id']}/status",
        headers=auth_header(admin_token),
        json={"status": "REJECTED", "rejected_reason": "Địa chỉ không rõ ràng"},
    )

    response = client.patch(
        COMPANY,
        headers=auth_header(employer["token"]),
        json={"headquarters_address": "47 Nguyễn Tuân, Thanh Xuân, Hà Nội"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"
    assert response.json()["rejected_reason"] is None


def test_changing_company_name_clears_the_tax_code_verification_mark(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    employer = make_employer()

    response = client.patch(
        COMPANY, headers=auth_header(employer["token"]), json={"company_name": "TÊN HOÀN TOÀN KHÁC"}
    )

    assert response.json()["tax_code_verified_at"] is None


# ─────────────────────────── Địa chỉ văn phòng ───────────────────────────


def test_employer_can_add_and_remove_addresses(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    employer = make_employer()
    headers = auth_header(employer["token"])

    created = client.post(
        ADDRESSES, headers=headers, json={"city_id": 1, "address_detail": "47 Nguyễn Tuân"}
    )
    assert created.status_code == 201
    address_id = created.json()["id"]
    assert len(client.get(COMPANY, headers=headers).json()["addresses"]) == 1

    assert client.delete(f"{ADDRESSES}/{address_id}", headers=headers).status_code == 204
    assert client.get(COMPANY, headers=headers).json()["addresses"] == []


def test_address_rejects_unknown_city(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    employer = make_employer()

    response = client.post(
        ADDRESSES,
        headers=auth_header(employer["token"]),
        json={"city_id": 9999, "address_detail": "Địa chỉ nào đó"},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CITY_NOT_FOUND"


def test_employer_cannot_delete_another_companys_address(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    """Biết đúng id địa chỉ của công ty khác cũng không xoá được."""
    alpha = make_employer("CÔNG TY TNHH ALPHA")
    beta = make_employer("CÔNG TY TNHH BETA")
    alpha_address_id = client.post(
        ADDRESSES,
        headers=auth_header(alpha["token"]),
        json={"city_id": 1, "address_detail": "Địa chỉ của Alpha"},
    ).json()["id"]

    response = client.delete(
        f"{ADDRESSES}/{alpha_address_id}", headers=auth_header(beta["token"])
    )

    assert response.status_code == 404
    # Xác nhận địa chỉ vẫn còn nguyên.
    assert len(client.get(COMPANY, headers=auth_header(alpha["token"])).json()["addresses"]) == 1
