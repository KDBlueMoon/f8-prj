"""Tin tuyển dụng phía nhà tuyển dụng.

Trọng tâm là các bất biến ở DESIGN mục 4.3: công ty chưa duyệt không đăng được
tin, tin bị gỡ không tự lên lại, và không NTD nào chạm được tin của NTD khác.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.conftest import auth_header

JOBS = "/api/v1/employer/jobs"


def _create(
    client: TestClient, token: str, payload: dict
) -> tuple[int, dict]:
    response = client.post(JOBS, headers=auth_header(token), json=payload)
    return response.status_code, response.json()


# ─────────────────────────── Tạo tin ───────────────────────────


def test_approved_company_can_publish_immediately(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Tin không qua bước duyệt: công ty đã APPROVED thì bấm đăng là lên ngay."""
    employer = make_approved_employer()

    code, body = _create(client, employer["token"], job_payload(status="PUBLISHED"))

    assert code == 201
    assert body["status"] == "PUBLISHED"
    assert body["slug"].startswith("lap-trinh-vien-backend-python-")
    assert body["company_id"] == employer["company_id"]


def test_pending_company_cannot_publish(
    client: TestClient,
    make_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Bất biến quan trọng nhất của P3."""
    employer = make_employer()

    code, body = _create(client, employer["token"], job_payload(status="PUBLISHED"))

    assert code == 403
    assert body["detail"]["code"] == "COMPANY_NOT_APPROVED"


def test_pending_company_can_still_save_a_draft(
    client: TestClient,
    make_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Chưa được duyệt vẫn soạn tin trước được — chỉ không đăng lên."""
    employer = make_employer()

    code, body = _create(client, employer["token"], job_payload())

    assert code == 201
    assert body["status"] == "DRAFT"


def test_html_is_sanitized_before_it_reaches_the_database(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Lớp chống XSS phải nằm ở backend, không chỉ ở trình duyệt."""
    employer = make_approved_employer()

    code, body = _create(
        client,
        employer["token"],
        job_payload(
            description_html='<p>Mô tả</p><script>alert("xss")</script>',
            requirements_html='<p onclick="steal()">Yêu cầu</p>',
        ),
    )

    assert code == 201
    assert body["description_html"] == "<p>Mô tả</p>"
    assert body["requirements_html"] == "<p>Yêu cầu</p>"


def test_empty_rich_text_is_rejected(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """`<p></p>` là trình soạn thảo rỗng, không phải nội dung."""
    employer = make_approved_employer()

    code, _ = _create(client, employer["token"], job_payload(description_html="<p><br></p>"))

    assert code == 422


def test_deadline_in_the_past_is_rejected(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()

    code, _ = _create(client, employer["token"], job_payload(deadline=past))

    assert code == 422


def test_salary_range_needs_both_numbers(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()

    code, body = _create(
        client, employer["token"], job_payload(salary_type="RANGE", salary_max=None)
    )

    assert code == 400
    assert body["detail"]["code"] == "SALARY_REQUIRED"


def test_agreement_salary_must_not_carry_numbers(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Lương thoả thuận mà vẫn gửi con số thì hiển thị ra sẽ mâu thuẫn."""
    employer = make_approved_employer()

    code, body = _create(client, employer["token"], job_payload(salary_type="AGREEMENT"))

    assert code == 400
    assert body["detail"]["code"] == "SALARY_NOT_ALLOWED"


def test_max_below_min_is_rejected(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()

    code, body = _create(
        client, employer["token"], job_payload(salary_min=40_000_000, salary_max=10_000_000)
    )

    assert code == 400
    assert body["detail"]["code"] == "SALARY_RANGE_INVALID"


def test_unknown_category_is_rejected(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()

    code, body = _create(
        client,
        employer["token"],
        job_payload(category_id="00000000-0000-0000-0000-000000000000"),
    )

    assert code == 404
    assert body["detail"]["code"] == "CATEGORY_NOT_FOUND"


def test_unknown_city_is_rejected(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()

    code, body = _create(
        client, employer["token"], job_payload(locations=[{"city_id": 9999}])
    )

    assert code == 404
    assert body["detail"]["code"] == "CITY_NOT_FOUND"


def test_a_job_needs_at_least_one_location(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()

    code, _ = _create(client, employer["token"], job_payload(locations=[]))

    assert code == 422


# ─────────────────────────── Sửa và xoá ───────────────────────────


def test_employer_can_edit_own_job(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    _, job = _create(client, employer["token"], job_payload())

    response = client.patch(
        f"{JOBS}/{job['id']}",
        headers=auth_header(employer["token"]),
        json={"title": "Kỹ sư dữ liệu", "quantity": 5},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Kỹ sư dữ liệu"
    assert response.json()["quantity"] == 5


def test_editing_the_title_keeps_the_slug(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Slug nằm trong URL công khai — đổi là gãy mọi link đã chia sẻ."""
    employer = make_approved_employer()
    _, job = _create(client, employer["token"], job_payload())

    response = client.patch(
        f"{JOBS}/{job['id']}",
        headers=auth_header(employer["token"]),
        json={"title": "Một tiêu đề hoàn toàn khác"},
    )

    assert response.json()["slug"] == job["slug"]


def test_switching_to_agreement_salary_clears_the_numbers(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Chỉ gửi salary_type mà vẫn phải hợp lệ — không bắt client gửi kèm null."""
    employer = make_approved_employer()
    _, job = _create(client, employer["token"], job_payload())

    response = client.patch(
        f"{JOBS}/{job['id']}",
        headers=auth_header(employer["token"]),
        json={"salary_type": "AGREEMENT"},
    )

    assert response.status_code == 200
    assert response.json()["salary_min"] is None
    assert response.json()["salary_max"] is None


def test_replacing_locations_removes_the_old_ones(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    _, job = _create(client, employer["token"], job_payload())

    response = client.patch(
        f"{JOBS}/{job['id']}",
        headers=auth_header(employer["token"]),
        json={"locations": [{"city_id": 2, "address_detail": "Quận 1"}]},
    )

    assert response.status_code == 200
    assert [item["city_id"] for item in response.json()["locations"]] == [2]


def test_deleted_job_disappears_from_the_list(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    headers = auth_header(employer["token"])
    _, job = _create(client, employer["token"], job_payload())

    assert client.delete(f"{JOBS}/{job['id']}", headers=headers).status_code == 204
    assert client.get(f"{JOBS}/{job['id']}", headers=headers).status_code == 404
    assert client.get(JOBS, headers=headers).json()["meta"]["total"] == 0


# ─────────────────────────── Chuyển trạng thái ───────────────────────────


def test_draft_can_be_published_then_closed_then_reopened(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    headers = auth_header(employer["token"])
    _, job = _create(client, employer["token"], job_payload())
    url = f"{JOBS}/{job['id']}/status"

    assert client.patch(url, headers=headers, json={"status": "PUBLISHED"}).json()["status"] == (
        "PUBLISHED"
    )
    assert client.patch(url, headers=headers, json={"status": "CLOSED"}).json()["status"] == "CLOSED"
    assert client.patch(url, headers=headers, json={"status": "PUBLISHED"}).json()["status"] == (
        "PUBLISHED"
    )


def test_employer_cannot_set_taken_down_or_expired(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Hai trạng thái này thuộc quyền admin và hệ thống, không phải NTD."""
    employer = make_approved_employer()
    _, job = _create(client, employer["token"], job_payload())

    for forbidden in ("TAKEN_DOWN", "EXPIRED"):
        response = client.patch(
            f"{JOBS}/{job['id']}/status",
            headers=auth_header(employer["token"]),
            json={"status": forbidden},
        )
        assert response.status_code == 422


def test_publishing_is_blocked_while_the_company_is_pending(
    client: TestClient,
    make_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_employer()
    _, job = _create(client, employer["token"], job_payload())

    response = client.patch(
        f"{JOBS}/{job['id']}/status",
        headers=auth_header(employer["token"]),
        json={"status": "PUBLISHED"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "COMPANY_NOT_APPROVED"


def test_taken_down_job_cannot_be_republished_directly(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    """Nếu bấm đăng lại được ngay thì quyết định gỡ tin của admin vô nghĩa."""
    employer = make_approved_employer()
    _, job = _create(client, employer["token"], job_payload(status="PUBLISHED"))
    client.patch(
        f"/api/v1/admin/jobs/{job['id']}/takedown",
        headers=auth_header(admin_token),
        json={"takedown_reason": "Nội dung sai sự thật"},
    )

    response = client.patch(
        f"{JOBS}/{job['id']}/status",
        headers=auth_header(employer["token"]),
        json={"status": "PUBLISHED"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "JOB_TAKEN_DOWN"


def test_editing_a_taken_down_job_puts_it_back_to_draft(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    """Đường duy nhất để tin bị gỡ quay lại: sửa nội dung rồi đăng lại."""
    employer = make_approved_employer()
    headers = auth_header(employer["token"])
    _, job = _create(client, employer["token"], job_payload(status="PUBLISHED"))
    client.patch(
        f"/api/v1/admin/jobs/{job['id']}/takedown",
        headers=auth_header(admin_token),
        json={"takedown_reason": "Nội dung sai sự thật"},
    )

    edited = client.patch(
        f"{JOBS}/{job['id']}",
        headers=headers,
        json={"description_html": "<p>Mô tả đã sửa lại cho đúng</p>"},
    ).json()

    assert edited["status"] == "DRAFT"
    assert edited["takedown_reason"] is None
    assert (
        client.patch(
            f"{JOBS}/{job['id']}/status", headers=headers, json={"status": "PUBLISHED"}
        ).json()["status"]
        == "PUBLISHED"
    )


# ─────────────────────────── Ranh giới giữa các công ty ───────────────────────────


def test_employer_only_sees_own_jobs(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    alpha = make_approved_employer("CÔNG TY TNHH ALPHA")
    beta = make_approved_employer("CÔNG TY TNHH BETA")
    _create(client, alpha["token"], job_payload(title="Tin của Alpha"))

    beta_list = client.get(JOBS, headers=auth_header(beta["token"])).json()

    assert beta_list["meta"]["total"] == 0


def test_employer_cannot_read_or_edit_another_companys_job(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Biết đúng id vẫn chỉ nhận 404 — không lộ cả sự tồn tại của tin."""
    alpha = make_approved_employer("CÔNG TY TNHH ALPHA")
    beta = make_approved_employer("CÔNG TY TNHH BETA")
    _, job = _create(client, alpha["token"], job_payload())
    beta_headers = auth_header(beta["token"])

    assert client.get(f"{JOBS}/{job['id']}", headers=beta_headers).status_code == 404
    assert (
        client.patch(f"{JOBS}/{job['id']}", headers=beta_headers, json={"quantity": 9}).status_code
        == 404
    )
    assert client.delete(f"{JOBS}/{job['id']}", headers=beta_headers).status_code == 404


def test_candidate_cannot_touch_employer_jobs(
    client: TestClient, make_candidate: Callable[[], str]
) -> None:
    response = client.get(JOBS, headers=auth_header(make_candidate()))

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN_ROLE"


def test_anonymous_cannot_touch_employer_jobs(client: TestClient) -> None:
    assert client.get(JOBS).status_code == 401


# ─────────────────────────── Danh sách và bộ đếm ───────────────────────────


def test_list_filters_by_status_and_keyword(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    headers = auth_header(employer["token"])
    _create(client, employer["token"], job_payload(title="Chuyên viên tuyển dụng"))
    _create(
        client,
        employer["token"],
        job_payload(title="Lập trình viên Frontend", status="PUBLISHED"),
    )

    published = client.get(f"{JOBS}?status=PUBLISHED", headers=headers).json()
    searched = client.get(f"{JOBS}?q=tuyển dụng", headers=headers).json()

    assert published["meta"]["total"] == 1
    assert published["items"][0]["title"] == "Lập trình viên Frontend"
    assert searched["meta"]["total"] == 1
    assert searched["items"][0]["title"] == "Chuyên viên tuyển dụng"


def test_counts_cover_every_status(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Trả đủ mọi khoá kể cả bằng 0 để tab trên giao diện không bị thiếu."""
    employer = make_approved_employer()
    _create(client, employer["token"], job_payload())
    _create(client, employer["token"], job_payload(status="PUBLISHED"))

    counts = client.get(f"{JOBS}/counts", headers=auth_header(employer["token"])).json()

    assert counts == {
        "DRAFT": 1,
        "PUBLISHED": 1,
        "CLOSED": 0,
        "EXPIRED": 0,
        "TAKEN_DOWN": 0,
    }
