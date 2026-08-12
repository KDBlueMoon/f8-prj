"""Luật kiểm tra dùng chung cho nhiều schema.

Gom về một chỗ để số điện thoại hay mã số thuế chỉ có duy nhất một định nghĩa —
sửa luật ở đây là mọi form đều theo, không sợ chỗ chặt chỗ lỏng.
"""

import re

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

_PHONE_PATTERN = re.compile(r"^0\d{9,10}$")
_TAX_CODE_PATTERN = re.compile(r"^\d{10}$|^\d{13}$")

PHONE_ERROR = "Số điện thoại phải gồm 10-11 chữ số và bắt đầu bằng 0."
TAX_CODE_ERROR = "Mã số thuế phải gồm 10 hoặc 13 chữ số."


def clean_phone(value: str) -> str:
    """Bỏ dấu cách và dấu chấm người dùng hay gõ xen vào số điện thoại."""
    return value.replace(" ", "").replace(".", "").replace("-", "")


def validate_required_phone(value: str) -> str:
    cleaned = clean_phone(value)
    if not _PHONE_PATTERN.match(cleaned):
        raise ValueError(PHONE_ERROR)
    return cleaned


def validate_optional_phone(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return validate_required_phone(value)


def validate_tax_code(value: str) -> str:
    cleaned = value.strip().replace(" ", "")
    if not _TAX_CODE_PATTERN.match(cleaned):
        raise ValueError(TAX_CODE_ERROR)
    return cleaned


def validate_password(value: str) -> str:
    """Yêu cầu tối thiểu: đủ dài, có cả chữ và số.

    Cố tình không bắt ký tự đặc biệt — quy tắc càng rườm rà người dùng càng hay
    đặt mật khẩu dễ đoán kiểu "Abc@1234".
    """
    # Đếm độ dài sau khi bỏ khoảng trắng hai đầu: "       1a" đủ 8 ký tự theo
    # min_length nhưng thực chất chỉ có 2 ký tự có nghĩa. Không tự cắt khoảng
    # trắng vì như vậy là âm thầm đổi mật khẩu người dùng đã nhập.
    if len(value.strip()) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Mật khẩu phải có tối thiểu {MIN_PASSWORD_LENGTH} ký tự, "
            "không tính khoảng trắng ở đầu và cuối."
        )
    if not any(char.isalpha() for char in value):
        raise ValueError("Mật khẩu phải có ít nhất một chữ cái.")
    if not any(char.isdigit() for char in value):
        raise ValueError("Mật khẩu phải có ít nhất một chữ số.")
    return value
