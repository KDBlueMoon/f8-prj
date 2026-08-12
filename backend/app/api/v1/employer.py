import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.core.deps import require_employer
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.company import (
    CompanyAddressIn,
    CompanyAddressOut,
    CompanyOut,
    CompanyUpdateIn,
)
from app.services import company_service

router = APIRouter(prefix="/employer", tags=["employer"])


@router.get("/company", response_model=CompanyOut)
def get_my_company(
    user: User = Depends(require_employer), db: Session = Depends(get_db)
) -> CompanyOut:
    """Hồ sơ công ty của chính tài khoản đang đăng nhập.

    Không nhận company_id từ client: công ty được suy ra từ token, nên không có
    cách nào xem hồ sơ của công ty khác.
    """
    return CompanyOut.model_validate(company_service.get_own_company(db, user))


@router.patch("/company", response_model=CompanyOut)
def update_my_company(
    payload: CompanyUpdateIn,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> CompanyOut:
    company = company_service.get_own_company(db, user)
    return CompanyOut.model_validate(company_service.update_own_company(db, company, payload))


@router.post(
    "/company/addresses", response_model=CompanyAddressOut, status_code=status.HTTP_201_CREATED
)
def add_company_address(
    payload: CompanyAddressIn,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> CompanyAddressOut:
    company = company_service.get_own_company(db, user)
    return CompanyAddressOut.model_validate(company_service.add_address(db, company, payload))


@router.delete("/company/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_address(
    address_id: uuid.UUID,
    user: User = Depends(require_employer),
    db: Session = Depends(get_db),
) -> None:
    company = company_service.get_own_company(db, user)
    company_service.delete_address(db, company, address_id)
