"""Nạp dữ liệu danh mục. Chạy: `python -m seeds.run`

Idempotent: chạy lại nhiều lần không tạo bản ghi trùng và không ghi đè dữ liệu
người dùng đã sửa — chỉ thêm bản ghi còn thiếu. Nhờ vậy để trong lệnh khởi động
của container cũng an toàn.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.catalog import Category, CategoryGroup, City
from app.db.session import SessionLocal
from seeds.data_categories import CATEGORY_GROUPS
from seeds.data_cities import CITIES


def seed_cities(db: Session) -> int:
    existing_ids = set(db.scalars(select(City.id)).all())
    created = 0
    for city_id, name, slug, is_municipality in CITIES:
        if city_id in existing_ids:
            continue
        db.add(City(id=city_id, name=name, slug=slug, is_municipality=is_municipality))
        created += 1
    return created


def seed_categories(db: Session) -> tuple[int, int]:
    groups_created = 0
    categories_created = 0

    # display_order lấy theo thứ tự khai báo trong data_categories.py — giữ
    # đúng thứ tự curated của data.json thay vì sắp theo alphabet.
    for group_order, (group_name, group_slug, categories) in enumerate(CATEGORY_GROUPS):
        group = db.scalar(select(CategoryGroup).where(CategoryGroup.group_slug == group_slug))
        if group is None:
            group = CategoryGroup(
                group_name=group_name, group_slug=group_slug, display_order=group_order
            )
            db.add(group)
            # flush để có group.id dùng cho category bên dưới, chưa commit.
            db.flush()
            groups_created += 1

        for category_order, (category_name, category_slug) in enumerate(categories):
            exists = db.scalar(select(Category.id).where(Category.slug == category_slug))
            if exists is not None:
                continue
            db.add(
                Category(
                    group_id=group.id,
                    name=category_name,
                    slug=category_slug,
                    display_order=category_order,
                )
            )
            categories_created += 1

    return groups_created, categories_created


def main() -> None:
    db = SessionLocal()
    try:
        cities = seed_cities(db)
        groups, categories = seed_categories(db)
        db.commit()
        print(
            f"[seed] cities: +{cities} | category_groups: +{groups} | categories: +{categories}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
