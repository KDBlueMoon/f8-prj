from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Kiểm tra app sống và kết nối được DB.

    Trả 503 khi DB hỏng để orchestrator/healthcheck nhận biết đúng, thay vì
    báo 200 rồi request nghiệp vụ mới lỗi.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "disconnected"},
        )
    return JSONResponse(content={"status": "ok", "database": "connected"})
