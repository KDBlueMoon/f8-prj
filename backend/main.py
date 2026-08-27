from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from middlewares.auth import SessionCleanupMiddleware
from routers import candidate, categories, companies, employer, jobs
from routers.auth import router as auth_router

app = FastAPI(
    title="TopCV Clone API",
    version="1.1.0",
    docs_url=None if settings.is_production else "/docs",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(SessionCleanupMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
def handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail, "code": exc.status_code})


@app.exception_handler(RequestValidationError)
def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"message": "Dữ liệu không hợp lệ", "code": 422})


@app.get("/api/v1/health", tags=["Public"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(employer.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(candidate.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
