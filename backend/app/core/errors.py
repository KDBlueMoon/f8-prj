from starlette import status


class AppError(Exception):
    """Lỗi nghiệp vụ có mã định danh, để FE bắt theo `code` thay vì so chuỗi.

    Message viết bằng tiếng Việt, hiển thị thẳng cho người dùng — không đưa
    chi tiết kỹ thuật (tên bảng, câu SQL, stack trace) vào đây.
    """

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status.HTTP_404_NOT_FOUND)


class ForbiddenError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status.HTTP_409_CONFLICT)
