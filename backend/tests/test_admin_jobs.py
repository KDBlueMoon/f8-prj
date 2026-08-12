"""Giám sát tin tuyển dụng phía quản trị viên.

Tin không qua bước duyệt (DESIGN mục 11.2), nên quyền gỡ tin của admin là chốt
kiểm soát duy nhất — phần này phải chắc.
"""

from collections.abc import Callable

from fastapi.testclient import TestClient

from tests.conftest import auth_header

ADMIN_JOBS = "/api/v1/admin/jobs"
EMPLOYER_JOBS = "/api/v1/employer/jobs"


def _publish(client: TestClient, employer: dict, payload: dict) -> dict:
    return client.post(
        EMPLOYER_JOBS, headers=auth_header(employer["token"]), json={**payload, "status": "PUBLISHED"}
    ).json()


def test_admin_sees_jobs_of_every_company(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    alpha = make_approved_employer("CÔNG TY TNHH ALPHA")
    _publish(client, alpha, job_payload(title="Tin cần giám sát"))

    listing = client.get(
        f"{ADMIN_JOBS}?company_id={alpha['company_id']}", headers=auth_header(admin_token)
    ).json()

    assert listing["meta"]["total"] == 1
    item = listing["items"][0]
    assert item["title"] == "Tin cần giám sát"
    # Admin xem tin của mọi công ty nên phải biết tin thuộc về ai.
    assert item["company"]["company_name"] == "CÔNG TY TNHH ALPHA"


def test_admin_can_take_down_a_job_with_a_reason(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())

    response = client.patch(
        f"{ADMIN_JOBS}/{job['id']}/takedown",
        headers=auth_header(admin_token),
        json={"takedown_reason": "Tin có dấu hiệu lừa đảo"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "TAKEN_DOWN"
    assert response.json()["takedown_reason"] == "Tin có dấu hiệu lừa đảo"


def test_takedown_requires_a_reason(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    """Không có lý do thì nhà tuyển dụng không biết phải sửa gì."""
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())

    response = client.patch(
        f"{ADMIN_JOBS}/{job['id']}/takedown",
        headers=auth_header(admin_token),
        json={"takedown_reason": ""},
    )

    assert response.status_code == 422


def test_taking_down_twice_is_rejected(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())
    headers = auth_header(admin_token)
    body = {"takedown_reason": "Tin có dấu hiệu lừa đảo"}
    client.patch(f"{ADMIN_JOBS}/{job['id']}/takedown", headers=headers, json=body)

    response = client.patch(f"{ADMIN_JOBS}/{job['id']}/takedown", headers=headers, json=body)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "JOB_ALREADY_TAKEN_DOWN"


def test_only_published_jobs_can_be_marked_hot(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    """Gắn nhãn nổi bật cho tin nháp thì nhãn đó chẳng hiển thị ở đâu."""
    employer = make_approved_employer()
    draft = client.post(
        EMPLOYER_JOBS, headers=auth_header(employer["token"]), json=job_payload()
    ).json()

    response = client.patch(
        f"{ADMIN_JOBS}/{draft['id']}/hot", headers=auth_header(admin_token), json={"is_hot": True}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "JOB_NOT_PUBLISHED"


def test_admin_can_toggle_hot_on_a_published_job(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())
    headers = auth_header(admin_token)

    assert (
        client.patch(f"{ADMIN_JOBS}/{job['id']}/hot", headers=headers, json={"is_hot": True}).json()[
            "is_hot"
        ]
        is True
    )
    assert (
        client.patch(
            f"{ADMIN_JOBS}/{job['id']}/hot", headers=headers, json={"is_hot": False}
        ).json()["is_hot"]
        is False
    )


def test_employer_cannot_use_admin_job_endpoints(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """NTD tự gỡ hoặc tự gắn nhãn nổi bật cho tin mình thì hai tính năng vô nghĩa."""
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())
    headers = auth_header(employer["token"])

    assert client.get(ADMIN_JOBS, headers=headers).status_code == 403
    assert (
        client.patch(
            f"{ADMIN_JOBS}/{job['id']}/takedown", headers=headers, json={"takedown_reason": "Tự gỡ"}
        ).status_code
        == 403
    )
    assert (
        client.patch(f"{ADMIN_JOBS}/{job['id']}/hot", headers=headers, json={"is_hot": True}).status_code
        == 403
    )


def test_rejecting_a_company_takes_down_all_of_its_published_jobs(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    """Bất biến DESIGN mục 4.3, chạy trong cùng transaction với việc từ chối.

    Không có bước này thì công ty bị từ chối vẫn còn tin nằm trên trang công khai.
    """
    employer = make_approved_employer()
    published = _publish(client, employer, job_payload(title="Tin đang chạy"))
    draft = client.post(
        EMPLOYER_JOBS, headers=auth_header(employer["token"]), json=job_payload(title="Tin nháp")
    ).json()

    client.patch(
        f"/api/v1/admin/companies/{employer['company_id']}/status",
        headers=auth_header(admin_token),
        json={"status": "REJECTED", "rejected_reason": "Giấy tờ không hợp lệ"},
    )

    employer_headers = auth_header(employer["token"])
    after_published = client.get(f"{EMPLOYER_JOBS}/{published['id']}", headers=employer_headers).json()
    after_draft = client.get(f"{EMPLOYER_JOBS}/{draft['id']}", headers=employer_headers).json()

    assert after_published["status"] == "TAKEN_DOWN"
    assert "Giấy tờ không hợp lệ" in after_published["takedown_reason"]
    # Tin nháp vốn không hiển thị công khai nên không cần đụng tới.
    assert after_draft["status"] == "DRAFT"


def test_approving_a_company_does_not_touch_its_jobs(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())

    client.patch(
        f"/api/v1/admin/companies/{employer['company_id']}/status",
        headers=auth_header(admin_token),
        json={"status": "APPROVED"},
    )

    after = client.get(
        f"{EMPLOYER_JOBS}/{job['id']}", headers=auth_header(employer["token"])
    ).json()
    assert after["status"] == "PUBLISHED"
