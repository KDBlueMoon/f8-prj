import uuid

from pydantic import BaseModel, ConfigDict


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    is_municipality: bool


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class CategoryGroupOut(BaseModel):
    """Trả về đúng dạng cây như category_groups trong data.json mẫu."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_name: str
    group_slug: str
    categories: list[CategoryOut]
