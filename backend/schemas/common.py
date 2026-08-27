from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: str
    code: int


class Address(BaseModel):
    model_config = {"from_attributes": True}

    city_id: int | None = None
    city_name: str | None = None
    address_detail: str | None = None
