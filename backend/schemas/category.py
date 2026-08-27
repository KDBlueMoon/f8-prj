import uuid

from pydantic import BaseModel


class CategoryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str


class CategoryGroupOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    group_name: str
    group_slug: str
    categories: list[CategoryOut]
