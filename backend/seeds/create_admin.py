"""Tạo tài khoản quản trị viên.

    docker exec -it f8_backend python -m seeds.create_admin --email admin@congty.vn

Mật khẩu nhập qua biến môi trường ADMIN_PASSWORD hoặc gõ trực tiếp khi được hỏi
(không hiện trên màn hình). Cố ý KHÔNG seed tự động: tài khoản admin với mật
khẩu mặc định nằm trong repo là lỗ hổng, ai đọc mã nguồn cũng đăng nhập được.
"""

import argparse
import getpass
import os
import sys

from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import SessionLocal

MIN_PASSWORD_LENGTH = 8


class _EmailCheck(BaseModel):
    """Dùng đúng validator của endpoint đăng nhập.

    Nếu script tự kiểm theo luật riêng, sẽ tạo ra được tài khoản mà API từ chối
    (vd domain .local bị email-validator coi là tên dành riêng) — admin có tài
    khoản nhưng không bao giờ đăng nhập được.
    """

    email: EmailStr


def _validate_email(email: str) -> str:
    try:
        return str(_EmailCheck(email=email).email)
    except ValidationError:
        sys.exit(f"Lỗi: '{email}' không phải email hợp lệ để đăng nhập.")


def _read_password() -> str:
    password = os.environ.get("ADMIN_PASSWORD")
    if password:
        return password

    password = getpass.getpass("Mật khẩu cho tài khoản admin: ")
    if password != getpass.getpass("Nhập lại mật khẩu: "):
        sys.exit("Lỗi: hai lần nhập mật khẩu không khớp.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo tài khoản quản trị viên")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Quản trị viên")
    args = parser.parse_args()

    email = _validate_email(args.email)
    password = _read_password()
    if len(password.strip()) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Lỗi: mật khẩu phải có tối thiểu {MIN_PASSWORD_LENGTH} ký tự.")

    db = SessionLocal()
    try:
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            sys.exit(f"Lỗi: email {email} đã được đăng ký.")

        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
                full_name=args.name,
            )
        )
        db.commit()
        # In email để xác nhận, tuyệt đối không in mật khẩu ra log.
        print(f"[admin] Đã tạo tài khoản quản trị viên: {email}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
