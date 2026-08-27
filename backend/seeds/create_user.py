"""Tạo tài khoản test (candidate/employer/admin) ngoài luồng HTTP.

    docker exec -it f8_backend python -m seeds.create_user --email a@b.com --role candidate

Mật khẩu nhập qua biến môi trường SEED_USER_PASSWORD hoặc gõ trực tiếp khi
được hỏi (không hiện trên màn hình). Cố ý KHÔNG seed tự động: tài khoản với
mật khẩu mặc định nằm trong repo là lỗ hổng, ai đọc mã nguồn cũng đăng nhập
được. Chủ yếu dùng để tạo tài khoản Admin (không có endpoint HTTP nào cho vai
trò này) hoặc tài khoản Candidate/Employer test nhanh không qua flow đăng ký.
"""

import argparse
import getpass
import os
import sys

from pydantic import BaseModel, EmailStr, ValidationError

from config.database import session
from models.all import User  # noqa: F401 — import toàn bộ model để đăng ký FK
from models.enums import UserRole
from utils.security import hash_password

MIN_PASSWORD_LENGTH = 8


class _EmailCheck(BaseModel):
    email: EmailStr


def _validate_email(email: str) -> str:
    try:
        return str(_EmailCheck(email=email).email)
    except ValidationError:
        sys.exit(f"Lỗi: '{email}' không phải email hợp lệ.")


def _read_password() -> str:
    password = os.environ.get("SEED_USER_PASSWORD")
    if password:
        return password

    password = getpass.getpass("Mật khẩu: ")
    if password != getpass.getpass("Nhập lại mật khẩu: "):
        sys.exit("Lỗi: hai lần nhập mật khẩu không khớp.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo tài khoản test")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Người dùng")
    parser.add_argument(
        "--role", choices=[r.value.lower() for r in UserRole], default="candidate"
    )
    args = parser.parse_args()

    email = _validate_email(args.email)
    password = _read_password()
    if len(password.strip()) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Lỗi: mật khẩu phải có tối thiểu {MIN_PASSWORD_LENGTH} ký tự.")

    if User.get_list(email=email):
        sys.exit(f"Lỗi: email {email} đã được đăng ký.")

    try:
        User.create(
            email=email,
            password_hash=hash_password(password),
            role=UserRole(args.role.upper()),
            full_name=args.name,
        )
        session.commit()
        print(f"[seed] Đã tạo tài khoản {args.role}: {email}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.remove()


if __name__ == "__main__":
    main()
