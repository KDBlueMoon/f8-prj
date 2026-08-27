from fastapi import APIRouter, HTTPException, Query
from starlette import status

from models.company import Company
from models.enums import UserRole
from models.user import User
from schemas.company import CompanyOut, CompanyRegisterRequest
from utils.db import transaction
from utils.security import hash_password

router = APIRouter(tags=["Public"])

PAGE_SIZE = 20


@router.get("/companies")
def list_companies(page: int = Query(1, ge=1), keyword: str | None = None) -> dict:
    items, total = Company.search(keyword=keyword, limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE)
    return {"data": [CompanyOut.model_validate(c) for c in items], "total": total}


@router.post("/companies/register", tags=["Employer"], status_code=status.HTTP_201_CREATED)
@transaction
def register_company(payload: CompanyRegisterRequest) -> dict:
    if Company.get_list(tax_code=payload.tax_code):
        raise HTTPException(status.HTTP_409_CONFLICT, "Mã số thuế đã được đăng ký")
    if User.get_list(email=payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")

    company = Company.create(
        tax_code=payload.tax_code,
        company_name=payload.company_name,
        international_name=payload.international_name,
        short_name=payload.short_name,
        director=payload.director,
        headquarters_address=payload.headquarters_address,
        email=payload.email,
        phone_number=payload.phone_number,
        website=payload.website,
    )
    User.create(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.EMPLOYER,
        full_name=payload.company_name,
        company_id=company.id,
    )
    return {"message": "Đăng ký thành công"}
