from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette import status

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import AppError
from app.core.rate_limit import limiter

app = FastAPI(
    title="f8 TopCV Clone API",
    version="0.1.0",
    # Ẩn tài liệu API ở production để không phơi toàn bộ bề mặt endpoint.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Cần thiết để trình duyệt gửi kèm httpOnly cookie chứa refresh token (P1).
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    """Đưa mọi lỗi nghiệp vụ về một format duy nhất cho FE dễ xử lý."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RateLimitExceeded)
def handle_rate_limit(_: Request, __: RateLimitExceeded) -> JSONResponse:
    """Lỗi vượt hạn mức cũng trả về đúng format lỗi chung của hệ thống."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": {
                "code": "TOO_MANY_REQUESTS",
                "message": "Bạn thao tác quá nhanh. Vui lòng thử lại sau ít phút.",
            }
        },
    )


app.include_router(api_router)
