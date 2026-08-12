"""API công ty công khai."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from tests.conftest import auth_header

COMPANIES = "/api/v1/companies"
EMPLOYER_JOBS = "/api/v1/employer/jobs"


def _publish(client: TestClient, employer: dict, payload: dict) -> dict:
    return client.post(
        EMPLOYER_JOBS,
        headers=auth_header(employer["token"]),
        json={**payload, "status": "PUBLISHED"},
    ).json()


def _company_slug(client: TestClient, employer: dict) -> str:
    return client.get("/api/v1/employer/company", headers=auth_header(employer["token"])).json()[
        "slug"
    ]


def test_guest_sees_approved_companies(
    client: TestClient, make_approved_employer: Callable[..., dict]
) -> None:
    employer = make_approved_employer("CÔNG TY TNHH CÔNG KHAI")

    body = client.get(f"{COMPANIES}?q=CÔNG KHAI").json()

    assert body["meta"]["total"] == 1
    assert body["items"][0]["company_name"] == "CÔNG TY TNHH CÔNG KHAI"


def test_pending_company_is_not_listed(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    """Hồ sơ chờ duyệt chưa phải thứ để khách nhìn thấy."""
    make_employer("CÔNG TY TNHH CHỜ DUYỆT")

    body = client.get(f"{COMPANIES}?q=CHỜ DUYỆT").json()

    assert body["meta"]["total"] == 0


def test_pending_company_detail_returns_404(
    client: TestClient, make_employer: Callable[..., dict]
) -> None:
    employer = make_employer()
    slug = _company_slug(client, employer)

    response = client.get(f"{COMPANIES}/{slug}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "COMPANY_NOT_FOUND"


def test_company_page_lists_only_jobs_that_are_open(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    headers = auth_header(employer["token"])
    open_job = _publish(client, employer, job_payload(title="Tin đang tuyển"))
    client.post(EMPLOYER_JOBS, headers=headers, json=job_payload(title="Tin còn nháp"))
    closed = _publish(client, employer, job_payload(title="Tin đã đóng"))
    client.patch(f"{EMPLOYER_JOBS}/{closed['id']}/status", headers=headers, json={"status": "CLOSED"})

    body = client.get(f"{COMPANIES}/{_company_slug(client, employer)}").json()

    assert [job["slug"] for job in body["open_jobs"]] == [open_job["slug"]]


def test_open_job_count_shows_on_the_listing(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Số tin đang tuyển là thứ người tìm việc nhìn đầu tiên khi lướt danh sách."""
    employer = make_approved_employer("CÔNG TY TNHH ĐẾM TIN")
    _publish(client, employer, job_payload())
    _publish(client, employer, job_payload())
    client.post(EMPLOYER_JOBS, headers=auth_header(employer["token"]), json=job_payload())

    body = client.get(f"{COMPANIES}?q=ĐẾM TIN").json()

    # Chỉ đếm tin đang tuyển, tin nháp không tính.
    assert body["items"][0]["open_job_count"] == 2


def test_public_company_payload_hides_contact_details(
    client: TestClient, make_approved_employer: Callable[..., dict]
) -> None:
    employer = make_approved_employer()

    body = client.get(f"{COMPANIES}/{_company_slug(client, employer)}").json()

    for private_field in ("email", "phone_number", "director", "tax_code", "rejected_reason"):
        assert private_field not in body
    assert body["company_name"]


def test_filter_companies_by_category_group(
    client: TestClient, make_approved_employer: Callable[..., dict]
) -> None:
    """Công ty gắn ở mức nhóm ngành, khác với tin gắn ngành nghề cụ thể."""
    group_id = client.get("/api/v1/categories").json()[0]["id"]
    tagged = make_approved_employer("CÔNG TY TNHH CÓ NHÓM NGÀNH")
    make_approved_employer("CÔNG TY TNHH KHÔNG NHÓM NGÀNH")
    client.patch(
        "/api/v1/employer/company",
        headers=auth_header(tagged["token"]),
        json={"category_group_id": group_id},
    )

    found = [
        item["company_name"]
        for item in client.get(f"{COMPANIES}?q=NHÓM NGÀNH&group_id={group_id}").json()["items"]
    ]

    assert found == ["CÔNG TY TNHH CÓ NHÓM NGÀNH"]


def test_lookup_tax_code_route_still_wins_over_the_slug_route(client: TestClient) -> None:
    """`/companies/{slug}` đứng sau nên không được nuốt mất route tra cứu MST.

    Đây là loại lỗi chỉ lộ ra khi đổi thứ tự khai báo route, nên phải có test giữ.
    """
    response = client.get(f"{COMPANIES}/lookup-tax-code/0100109106")

    # VietQR bị mock thành không phản hồi trong test — điều cần khẳng định là
    # request rơi vào endpoint tra cứu chứ không phải endpoint chi tiết công ty.
    assert response.json()["detail"]["code"] == "TAX_LOOKUP_UNAVAILABLE"
