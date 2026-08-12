"""Import tất cả model ở một chỗ để Alembic autogenerate thấy đủ bảng."""

from app.db.base import Base
from app.db.models.application import Application, Cv, SavedJob
from app.db.models.catalog import Category, CategoryGroup, City
from app.db.models.company import Company, CompanyAddress, CompanyMember
from app.db.models.job import Job, JobLocation
from app.db.models.user import User

__all__ = [
    "Base",
    "Application",
    "Category",
    "CategoryGroup",
    "City",
    "Company",
    "CompanyAddress",
    "CompanyMember",
    "Cv",
    "Job",
    "JobLocation",
    "SavedJob",
    "User",
]
