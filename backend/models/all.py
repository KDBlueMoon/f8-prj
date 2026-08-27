"""Import toàn bộ model để đăng ký vào `Base.metadata` — dùng cho Alembic autogenerate.

Không có model nào tự động được biết tới nếu module của nó chưa từng được
import ở đâu đó trong tiến trình; file này tồn tại chỉ để đảm bảo import đó
luôn xảy ra trước khi Alembic so sánh metadata với DB.
"""

from config.database import Base
from models.application import Application
from models.category import Category, CategoryGroup
from models.company import Company
from models.cv import CV
from models.job import Job, JobLocation
from models.user import User

__all__ = [
    "Base",
    "User",
    "Company",
    "CategoryGroup",
    "Category",
    "Job",
    "JobLocation",
    "CV",
    "Application",
]
