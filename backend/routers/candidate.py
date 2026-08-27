from fastapi import APIRouter, Depends
from starlette import status

from middlewares.auth import require_role
from models.cv import CV
from models.enums import UserRole
from models.user import User
from schemas.cv import CVCreateResponse, CVCreationRequest
from utils.db import transaction

router = APIRouter(prefix="/candidate", tags=["Candidate"])


@router.post("/cvs", response_model=CVCreateResponse, status_code=status.HTTP_201_CREATED)
@transaction
def create_cv(
    payload: CVCreationRequest, current_user: User = Depends(require_role(UserRole.CANDIDATE))
) -> CVCreateResponse:
    cv = CV.create(
        user_id=current_user.id,
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        summary=payload.summary,
        education=[edu.model_dump() for edu in payload.education],
        experience=payload.experience,
        skills=payload.skills,
    )
    return CVCreateResponse(cv_id=cv.id)
