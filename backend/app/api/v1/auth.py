from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from starlette import status

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    CompanyBriefOut,
    LoginRequest,
    LoginResponse,
    MeOut,
    RegisterCandidateRequest,
    RegisterEmployerRequest,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_SECONDS_PER_MINUTE = 60
_SECONDS_PER_DAY = 86400
# Cookie chỉ được gửi kèm khi gọi các endpoint auth, không rải theo mọi request.
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        # httponly: JavaScript không đọc được -> XSS không lấy được token.
        httponly=True,
        # secure chỉ bật ở production vì dev chạy http://localhost.
        secure=settings.is_production,
        samesite="lax",
        path=_REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * _SECONDS_PER_DAY,
    )


def _login_response(db: Session, user: User, response: Response) -> LoginResponse:
    access_token, refresh_token = auth_service.issue_tokens(db, user)
    _set_refresh_cookie(response, refresh_token)

    company = auth_service.get_company_for_user(db, user)
    return LoginResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * _SECONDS_PER_MINUTE,
        user=UserOut.model_validate(user),
        company=CompanyBriefOut.model_validate(company) if company else None,
    )


@router.post("/register/candidate", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register_candidate(
    request: Request,
    payload: RegisterCandidateRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Đăng ký ứng viên và đăng nhập luôn, khỏi bắt nhập lại thông tin."""
    user = auth_service.register_candidate(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
    )
    return _login_response(db, user, response)


@router.post("/register/employer", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
def register_employer(
    request: Request,
    payload: RegisterEmployerRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Đăng ký nhà tuyển dụng kèm hồ sơ công ty.

    Đăng nhập được ngay, nhưng công ty ở trạng thái PENDING nên chưa đăng tin
    được cho tới khi admin duyệt (P2).
    """
    user, _ = auth_service.register_employer(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        company_info=payload.company,
    )
    return _login_response(db, user, response)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    return _login_response(db, user, response)


@router.post("/refresh", response_model=LoginResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    """Cấp access token mới từ refresh cookie, đồng thời luân chuyển refresh token."""
    raw_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_token:
        raise auth_service.invalid_refresh_token()

    user, access_token, new_refresh_token = auth_service.rotate_refresh_token(db, raw_token)
    _set_refresh_cookie(response, new_refresh_token)

    company = auth_service.get_company_for_user(db, user)
    return LoginResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * _SECONDS_PER_MINUTE,
        user=UserOut.model_validate(user),
        company=CompanyBriefOut.model_validate(company) if company else None,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)) -> Response:
    auth_service.revoke_refresh_token(db, request.cookies.get(settings.REFRESH_COOKIE_NAME))

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path=_REFRESH_COOKIE_PATH)
    return response


@router.get("/me", response_model=MeOut)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeOut:
    company = auth_service.get_company_for_user(db, user)
    return MeOut(
        user=UserOut.model_validate(user),
        company=CompanyBriefOut.model_validate(company) if company else None,
    )
