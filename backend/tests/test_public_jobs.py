"""API việc làm công khai.

Hai thứ phải chắc ở đây:
1. Cái gì **không** được lộ ra: tin nháp, tin đóng, tin bị gỡ, tin hết hạn, tin
   của công ty chưa duyệt.
2. Bộ lọc và sắp xếp trả về đúng tập kết quả.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.conftest import auth_header

JOBS = "/api/v1/jobs"
EMPLOYER_JOBS = "/api/v1/employer/jobs"


def _publish(client: TestClient, employer: dict, payload: dict) -> dict:
    """Đăng một tin PUBLISHED và trả về bản ghi tin."""
    return client.post(
        EMPLOYER_JOBS,
        headers=auth_header(employer["token"]),
        json={**payload, "status": "PUBLISHED"},
    ).json()


def _slugs(body: dict) -> list[str]:
    return [item["slug"] for item in body["items"]]


# ─────────────────────────── Truy cập công khai ───────────────────────────


def test_guest_can_browse_jobs_without_logging_in(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Mục tiêu kiểm chứng của P4."""
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload(title="Kỹ sư cầu nối tiếng Nhật"))

    listing = client.get(f"{JOBS}?q=cầu nối")
    detail = client.get(f"{JOBS}/{job['slug']}")

    assert listing.status_code == 200
    assert _slugs(listing.json()) == [job["slug"]]
    assert detail.status_code == 200
    assert detail.json()["title"] == "Kỹ sư cầu nối tiếng Nhật"


def test_detail_embeds_the_company_object(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Trả company lồng vào để frontend không phải gọi thêm một lượt."""
    employer = make_approved_employer("CÔNG TY TNHH LỒNG NHAU")
    job = _publish(client, employer, job_payload())

    company = client.get(f"{JOBS}/{job['slug']}").json()["company"]

    assert company["company_name"] == "CÔNG TY TNHH LỒNG NHAU"
    assert company["id"] == employer["company_id"]


def test_public_payload_never_leaks_private_company_fields(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Email và SĐT nhà tuyển dụng phơi ra là mời bot gửi rác."""
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())

    company = client.get(f"{JOBS}/{job['slug']}").json()["company"]

    for private_field in ("email", "phone_number", "director", "tax_code", "rejected_reason"):
        assert private_field not in company


def test_draft_and_closed_jobs_stay_hidden(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    headers = auth_header(employer["token"])
    draft = client.post(EMPLOYER_JOBS, headers=headers, json=job_payload()).json()
    closed = _publish(client, employer, job_payload())
    client.patch(f"{EMPLOYER_JOBS}/{closed['id']}/status", headers=headers, json={"status": "CLOSED"})

    assert client.get(f"{JOBS}/{draft['slug']}").status_code == 404
    assert client.get(f"{JOBS}/{closed['slug']}").status_code == 404


def test_taken_down_job_disappears_from_the_public_site(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())
    assert client.get(f"{JOBS}/{job['slug']}").status_code == 200

    client.patch(
        f"/api/v1/admin/jobs/{job['id']}/takedown",
        headers=auth_header(admin_token),
        json={"takedown_reason": "Nội dung sai sự thật"},
    )

    assert client.get(f"{JOBS}/{job['slug']}").status_code == 404


def test_rejecting_the_company_hides_its_jobs_from_the_public_site(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    """Nối trọn bất biến của P3 tới đầu ra công khai của P4."""
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())

    client.patch(
        f"/api/v1/admin/companies/{employer['company_id']}/status",
        headers=auth_header(admin_token),
        json={"status": "REJECTED", "rejected_reason": "Giấy tờ không hợp lệ"},
    )

    assert client.get(f"{JOBS}/{job['slug']}").status_code == 404


def test_expired_job_is_not_listed(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    db,
) -> None:
    """Cron chuyển EXPIRED chỉ chạy hằng ngày (P7), nên API phải tự lọc theo hạn.

    Không có điều kiện `deadline > now()` thì tin quá hạn vẫn hiện suốt tới lần
    cron kế tiếp và ứng viên nộp hồ sơ vào chỗ đã đóng.
    """
    from app.db.models.job import Job

    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())

    # Đẩy hạn về quá khứ nhưng giữ nguyên status PUBLISHED, đúng như lúc cron
    # chưa kịp chạy.
    db.get(Job, job["id"]).deadline = datetime.now(UTC) - timedelta(days=1)
    db.commit()

    assert client.get(f"{JOBS}/{job['slug']}").status_code == 404
    assert job["slug"] not in _slugs(client.get(f"{JOBS}?q={job['title']}").json())


def test_unknown_slug_returns_a_business_error_code(client: TestClient) -> None:
    response = client.get(f"{JOBS}/khong-ton-tai-dau-nhe-123456")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"


# ─────────────────────────── Bộ lọc ───────────────────────────


def test_filter_by_city_uses_the_job_locations(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    hanoi = _publish(client, employer, job_payload(locations=[{"city_id": 1}]))
    saigon = _publish(client, employer, job_payload(locations=[{"city_id": 2}]))

    found = _slugs(client.get(f"{JOBS}?city_id=2&q={saigon['title']}").json())

    assert saigon["slug"] in found
    assert hanoi["slug"] not in found


def test_a_job_with_many_locations_is_counted_once(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Lọc theo tỉnh/thành bằng JOIN sẽ nhân bản dòng và làm sai tổng số."""
    employer = make_approved_employer()
    job = _publish(
        client,
        employer,
        job_payload(
            title="Tin nhiều địa điểm",
            locations=[{"city_id": 1}, {"city_id": 2}, {"city_id": 3}],
        ),
    )

    body = client.get(f"{JOBS}?q=nhiều địa điểm").json()

    assert body["meta"]["total"] == 1
    assert _slugs(body) == [job["slug"]]


def test_filter_by_job_type_and_experience(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    intern = _publish(
        client,
        employer,
        job_payload(title="Thực tập sinh dữ liệu", job_type="INTERNSHIP", experience_level="NO_EXP"),
    )
    senior = _publish(
        client,
        employer,
        job_payload(title="Thực tập sinh dữ liệu cấp cao", experience_level="OVER_5"),
    )

    by_type = _slugs(client.get(f"{JOBS}?q=thực tập&job_type=INTERNSHIP").json())
    by_experience = _slugs(client.get(f"{JOBS}?q=thực tập&experience_level=OVER_5").json())

    assert by_type == [intern["slug"]]
    assert by_experience == [senior["slug"]]


def test_filter_by_category_group(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Lọc theo nhóm ngành phải gom hết ngành nghề con của nhóm đó."""
    groups = client.get("/api/v1/categories").json()
    first_group, second_group = groups[0], groups[1]
    employer = make_approved_employer()
    inside = _publish(
        client,
        employer,
        job_payload(title="Tin thuộc nhóm đầu", category_id=first_group["categories"][0]["id"]),
    )
    outside = _publish(
        client,
        employer,
        job_payload(title="Tin thuộc nhóm sau", category_id=second_group["categories"][0]["id"]),
    )

    found = _slugs(client.get(f"{JOBS}?group_id={first_group['id']}&q=Tin thuộc nhóm").json())

    assert inside["slug"] in found
    assert outside["slug"] not in found


def test_salary_filter_matches_overlapping_ranges(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    low = _publish(
        client,
        employer,
        job_payload(title="Lương thấp cần lọc", salary_min=8_000_000, salary_max=12_000_000),
    )
    high = _publish(
        client,
        employer,
        job_payload(title="Lương cao cần lọc", salary_min=40_000_000, salary_max=60_000_000),
    )

    at_least_30m = _slugs(client.get(f"{JOBS}?q=cần lọc&salary_min=30000000").json())

    assert at_least_30m == [high["slug"]]
    assert low["slug"] not in at_least_30m


def test_agreement_salary_drops_out_when_filtering_by_number(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    """Không có cách nào biết "thoả thuận" có đạt mức người dùng nhập hay không."""
    employer = make_approved_employer()
    agreement = _publish(
        client,
        employer,
        job_payload(
            title="Lương thoả thuận cần lọc",
            salary_type="AGREEMENT",
            salary_min=None,
            salary_max=None,
        ),
    )

    filtered = _slugs(client.get(f"{JOBS}?q=thoả thuận cần lọc&salary_min=1").json())
    unfiltered = _slugs(client.get(f"{JOBS}?q=thoả thuận cần lọc").json())

    assert filtered == []
    assert unfiltered == [agreement["slug"]]


def test_filter_by_hot_flag(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
    admin_token: str,
) -> None:
    employer = make_approved_employer()
    normal = _publish(client, employer, job_payload(title="Tin thường cần lọc"))
    hot = _publish(client, employer, job_payload(title="Tin nổi bật cần lọc"))
    client.patch(
        f"/api/v1/admin/jobs/{hot['id']}/hot",
        headers=auth_header(admin_token),
        json={"is_hot": True},
    )

    found = _slugs(client.get(f"{JOBS}?q=cần lọc&is_hot=true").json())

    assert found == [hot["slug"]]
    assert normal["slug"] not in found


# ─────────────────────────── Sắp xếp và phân trang ───────────────────────────


def test_sort_by_salary_puts_the_highest_first_and_agreement_last(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    low = _publish(
        client,
        employer,
        job_payload(title="Sắp lương mức thấp", salary_min=8_000_000, salary_max=10_000_000),
    )
    high = _publish(
        client,
        employer,
        job_payload(title="Sắp lương mức cao", salary_min=50_000_000, salary_max=70_000_000),
    )
    agreement = _publish(
        client,
        employer,
        job_payload(
            title="Sắp lương thoả thuận",
            salary_type="AGREEMENT",
            salary_min=None,
            salary_max=None,
        ),
    )

    ordered = _slugs(client.get(f"{JOBS}?q=Sắp lương&sort=salary_desc").json())

    assert ordered == [high["slug"], low["slug"], agreement["slug"]]


def test_sort_by_deadline_puts_the_soonest_first(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    later = _publish(
        client,
        employer,
        job_payload(
            title="Sắp hạn xa",
            deadline=(datetime.now(UTC) + timedelta(days=60)).isoformat(),
        ),
    )
    sooner = _publish(
        client,
        employer,
        job_payload(
            title="Sắp hạn gần",
            deadline=(datetime.now(UTC) + timedelta(days=2)).isoformat(),
        ),
    )

    ordered = _slugs(client.get(f"{JOBS}?q=Sắp hạn&sort=deadline").json())

    assert ordered == [sooner["slug"], later["slug"]]


def test_pagination_splits_the_result_set(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    for index in range(3):
        _publish(client, employer, job_payload(title=f"Tin phân trang số {index}"))

    first = client.get(f"{JOBS}?q=phân trang&page=1&page_size=2").json()
    second = client.get(f"{JOBS}?q=phân trang&page=2&page_size=2").json()

    assert first["meta"] == {"page": 1, "page_size": 2, "total": 3, "total_pages": 2}
    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    # Không có tin nào lọt vào cả hai trang.
    assert set(_slugs(first)) & set(_slugs(second)) == set()


def test_page_size_is_capped(client: TestClient) -> None:
    """Không cho khách tự nâng page_size để kéo cả bảng về trong một lượt."""
    assert client.get(f"{JOBS}?page_size=500").status_code == 422


def test_viewing_the_detail_page_counts_a_view(
    client: TestClient,
    make_approved_employer: Callable[..., dict],
    job_payload: Callable[..., dict],
) -> None:
    employer = make_approved_employer()
    job = _publish(client, employer, job_payload())

    first = client.get(f"{JOBS}/{job['slug']}").json()
    second = client.get(f"{JOBS}/{job['slug']}").json()

    assert first["view_count"] == job["view_count"] + 1
    assert second["view_count"] == first["view_count"] + 1
