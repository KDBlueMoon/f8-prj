"""Decorator quản lý transaction cho router — thay cho `Depends(get_db)`.

Router chỉ cần đọc/ghi qua `session` global (`config.database.session`) và bọc
hàm bằng `@transaction`: thành công thì commit, lỗi thì rollback rồi raise lại
nguyên vẹn (để exception handler ở `main.py` xử lý response), cuối cùng luôn
`session.remove()` để trả connection về pool.
"""

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from config.database import session

F = TypeVar("F", bound=Callable[..., Any])


def transaction(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = func(*args, **kwargs)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.remove()

    return wrapper  # type: ignore[return-value]
