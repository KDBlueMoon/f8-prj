"""Nạp dữ liệu danh mục ngành nghề. Chạy: `python -m seeds.run`

Idempotent: chạy lại nhiều lần không tạo bản ghi trùng — chỉ thêm bản ghi còn
thiếu. Nhờ vậy để trong lệnh khởi động của container cũng an toàn.
"""

from sqlalchemy import select

from config.database import session
from models.category import Category, CategoryGroup
from seeds.data_categories import CATEGORY_GROUPS


def seed_categories() -> tuple[int, int]:
    groups_created = 0
    categories_created = 0

    for group_order, (group_name, group_slug, categories) in enumerate(CATEGORY_GROUPS):
        group = session.scalar(select(CategoryGroup).where(CategoryGroup.group_slug == group_slug))
        if group is None:
            group = CategoryGroup(group_name=group_name, group_slug=group_slug, display_order=group_order)
            session.add(group)
            session.flush()
            groups_created += 1

        for category_order, (category_name, category_slug) in enumerate(categories):
            exists = session.scalar(select(Category.id).where(Category.slug == category_slug))
            if exists is not None:
                continue
            session.add(
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
    try:
        groups, categories = seed_categories()
        session.commit()
        print(f"[seed] category_groups: +{groups} | categories: +{categories}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.remove()


if __name__ == "__main__":
    main()
