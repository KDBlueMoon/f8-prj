"""Bật extension citext

Cần chạy trước khi tạo bảng vì cột email của users/companies dùng kiểu CITEXT
(so sánh không phân biệt hoa/thường ngay ở tầng DB).

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")


def downgrade() -> None:
    # Không DROP EXTENSION: nếu có schema khác trong cùng database đang dùng
    # citext thì sẽ hỏng. Rollback migration này chỉ cần bỏ các bảng phía sau.
    pass
