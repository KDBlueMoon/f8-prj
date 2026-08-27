# f8-prj — Clone TopCV

API nền tảng tuyển dụng: ứng viên tìm & ứng tuyển việc làm, nhà tuyển dụng đăng
tin. Hợp đồng API nằm ở [`openapi.yaml`](openapi.yaml) — đó là bản thiết kế
gốc, code viết theo đúng file đó (kèm 2 bổ sung nhỏ để luồng chạy được trọn
vẹn: `POST /auth/register` cho Candidate, và field `password` trong
`CompanyRegisterRequest`).

- **Backend:** FastAPI (Python) + PostgreSQL 16 + SQLAlchemy 2 + Alembic

---

## Chạy dự án

Yêu cầu: **Docker Desktop**. Không cần cài Python trên máy.

```bash
# 1. Tạo file cấu hình từ mẫu
cp .env.example .env

# 2. Điền 2 giá trị bắt buộc trong .env
#    POSTGRES_PASSWORD=<mật khẩu tự chọn>
#    SECRET_KEY=<sinh bằng: openssl rand -hex 32>

# 3. Khởi động các service
docker compose up -d
```

| Địa chỉ | Nội dung |
|---|---|
| http://localhost:8000/api/v1/health | Health check |
| http://localhost:8000/docs | Swagger UI (chỉ khi `APP_ENV != production`) |

Lệnh khởi động của container backend (`docker-compose.yml`) tự chạy
`alembic upgrade head` rồi `python -m seeds.run` (seed danh mục ngành nghề,
idempotent) trước khi bật server.

> ⚠️ **Không commit `.env`.** File này đã nằm trong `.gitignore`. Chỉ commit
> `.env.example` với giá trị rỗng.

---

## Lệnh thường dùng

```bash
docker compose logs -f backend        # xem log backend
docker compose down                   # dừng
# Data DB nằm ở bind mount ./pgdata (không phải named volume) — muốn xoá sạch
# để làm lại từ đầu thì rm -rf ./pgdata sau khi đã docker compose down.

# Tạo tài khoản test không qua HTTP (không có endpoint admin nào cả)
docker exec -it f8-prj-backend-1 poetry run python -m seeds.create_user --email a@b.com --role admin

# Migration
docker exec f8-prj-backend-1 poetry run alembic revision --autogenerate -m "mô tả"
docker exec f8-prj-backend-1 poetry run alembic upgrade head
docker exec f8-prj-backend-1 poetry run alembic check  # báo lỗi nếu model lệch migration
```

Chưa có bộ test tự động — bộ pytest cũ được viết cho schema/endpoint đời
trước, không còn khớp với API hiện tại nên đã xoá cùng phần backend cũ thay vì
cố sửa lại cho khớp một hợp đồng hoàn toàn khác.
