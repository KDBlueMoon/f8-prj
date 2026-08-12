"""Fixture dùng chung cho test.

Ở P0 test chỉ đọc dữ liệu danh mục đã seed nên dùng thẳng DB của môi trường
dev là an toàn. Từ P1 (có ghi dữ liệu) sẽ tách sang database test riêng.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Session luôn rollback ở cuối test — test không để lại rác trong DB."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
