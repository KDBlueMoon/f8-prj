from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# pool_pre_ping: kiểm tra connection còn sống trước khi dùng — tránh lỗi
# "server closed the connection unexpectedly" sau khi Postgres restart.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: mở session cho mỗi request và luôn đóng lại."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
