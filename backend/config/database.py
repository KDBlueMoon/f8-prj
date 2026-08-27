"""Engine + session dùng chung toàn app (kiểu ActiveRecord, không DI theo request).

`session` là một `scoped_session` toàn cục — models và routers import thẳng
biến này thay vì nhận qua `Depends(get_db)`. Đơn giản hơn cho quy mô API này,
đổi lại router phải nhớ dùng decorator `@transaction` (xem `utils/db.py`) để
commit/rollback đúng lúc.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from config.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
session = scoped_session(SessionLocal)


class Base(DeclarativeBase):
    pass
