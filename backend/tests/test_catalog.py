from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from seeds.data_categories import CATEGORY_GROUPS
from seeds.data_cities import CITIES
from seeds.run import seed_categories, seed_cities

EXPECTED_CITY_COUNT = 34
EXPECTED_MUNICIPALITY_COUNT = 6


def test_health_reports_database_connected(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_cities_seeded_with_34_units(client: TestClient) -> None:
    response = client.get("/api/v1/cities")

    assert response.status_code == 200
    cities = response.json()
    assert len(cities) == EXPECTED_CITY_COUNT


def test_cities_put_municipalities_first_with_ha_noi_leading(client: TestClient) -> None:
    """Hà Nội và TP.HCM phải đứng đầu dropdown chọn địa điểm."""
    cities = client.get("/api/v1/cities").json()

    municipalities = [city for city in cities if city["is_municipality"]]
    assert len(municipalities) == EXPECTED_MUNICIPALITY_COUNT
    # 6 phần tử đầu đều là TP trực thuộc TW, không bị tỉnh chen vào giữa.
    assert all(city["is_municipality"] for city in cities[:EXPECTED_MUNICIPALITY_COUNT])
    assert cities[0]["name"] == "Hà Nội"
    assert cities[1]["name"] == "Thành phố Hồ Chí Minh"


def test_city_ids_are_stable_for_data_json_compatibility(client: TestClient) -> None:
    """id 1/2 cố định vì data.json mẫu dùng city_id 1 = Hà Nội, 2 = TP.HCM."""
    cities = {city["id"]: city["name"] for city in client.get("/api/v1/cities").json()}

    assert cities[1] == "Hà Nội"
    assert cities[2] == "Thành phố Hồ Chí Minh"


def test_city_slugs_are_unique(client: TestClient) -> None:
    slugs = [city["slug"] for city in client.get("/api/v1/cities").json()]

    assert len(slugs) == len(set(slugs))


def test_categories_return_full_tree(client: TestClient) -> None:
    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    groups = response.json()
    assert len(groups) == len(CATEGORY_GROUPS)
    total_categories = sum(len(group["categories"]) for group in groups)
    assert total_categories == sum(len(categories) for _, _, categories in CATEGORY_GROUPS)


def test_categories_keep_declared_order_not_alphabetical(client: TestClient) -> None:
    """Thứ tự phải khớp data.json, không phụ thuộc collation tiếng Việt."""
    groups = client.get("/api/v1/categories").json()

    returned_slugs = [group["group_slug"] for group in groups]
    expected_slugs = [group_slug for _, group_slug, _ in CATEGORY_GROUPS]
    assert returned_slugs == expected_slugs


def test_every_group_has_at_least_one_category(client: TestClient) -> None:
    """jobs.category_id là NOT NULL nên nhóm nào cũng phải có ngành để chọn.

    Riêng "Lao động phổ thông" trong data.json không có mảng categories —
    seed phải tự bù một ngành mặc định.
    """
    groups = client.get("/api/v1/categories").json()

    for group in groups:
        assert group["categories"], f"Nhóm {group['group_slug']} không có ngành nghề nào"


def test_seed_is_idempotent(db: Session) -> None:
    """Chạy lại seed không được tạo thêm bản ghi trùng.

    Quan trọng vì lệnh khởi động container gọi seed mỗi lần restart.
    """
    assert seed_cities(db) == 0
    assert seed_categories(db) == (0, 0)


def test_seed_data_has_no_duplicate_ids_or_slugs() -> None:
    """Bắt lỗi copy/paste ngay trong file seed, trước khi chạm tới DB."""
    city_ids = [city_id for city_id, _, _, _ in CITIES]
    city_slugs = [slug for _, _, slug, _ in CITIES]
    assert len(city_ids) == len(set(city_ids))
    assert len(city_slugs) == len(set(city_slugs))

    category_slugs = [
        category_slug
        for _, _, categories in CATEGORY_GROUPS
        for _, category_slug in categories
    ]
    assert len(category_slugs) == len(set(category_slugs))
