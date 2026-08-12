# f8-prj — Clone TopCV

Nền tảng tuyển dụng: ứng viên tìm & ứng tuyển việc làm, nhà tuyển dụng đăng tin,
admin duyệt hồ sơ công ty.

- **Frontend:** Vite + React 19 + TypeScript + TailwindCSS 4
- **Backend:** FastAPI (Python 3.12) + PostgreSQL 16 + SQLAlchemy 2 + Alembic
- **Thiết kế chi tiết:** [`docs/DESIGN.md`](docs/DESIGN.md) · **Mockup UI:** [`docs/mockups/index.html`](docs/mockups/index.html)

---

## Chạy dự án

Yêu cầu: **Docker Desktop**. Không cần cài Python hay Node trên máy.

```bash
# 1. Tạo file cấu hình từ mẫu
cp .env.example .env

# 2. Điền 2 giá trị bắt buộc trong .env
#    POSTGRES_PASSWORD=<mật khẩu tự chọn>
#    SECRET_KEY=<sinh bằng: openssl rand -hex 32>

# 3. Khởi động cả 3 service
docker compose up -d
```

| Địa chỉ | Nội dung |
|---|---|
| http://localhost:5173 | Frontend |
| http://localhost:5173/dang-ky | Đăng ký ứng viên |
| http://localhost:5173/dang-ky/nha-tuyen-dung | Đăng ký nhà tuyển dụng |
| http://localhost:8000/api/v1/health | Health check |
| http://localhost:8000/docs | Swagger UI (chỉ khi `APP_ENV != production`) |

Backend tự chạy `alembic upgrade head` rồi seed danh mục mỗi lần khởi động.
Seed idempotent nên restart nhiều lần không sinh dữ liệu trùng.

> ⚠️ **Không commit `.env`.** File này đã nằm trong `.gitignore`. Chỉ commit
> `.env.example` với giá trị rỗng.

---

## Lệnh thường dùng

```bash
docker compose logs -f backend        # xem log backend
docker compose down                   # dừng (giữ dữ liệu DB)
docker compose down -v                # dừng và XOÁ SẠCH dữ liệu DB

docker exec f8_backend pytest -q      # chạy test backend
docker exec f8_frontend npm run build # type-check + build frontend

# Tạo tài khoản quản trị viên (nhập mật khẩu khi được hỏi, không hiện ra màn hình)
docker exec -it f8_backend python -m seeds.create_admin --email admin@congty.vn

# Migration
docker exec f8_backend alembic revision --autogenerate -m "mô tả"
docker exec f8_backend alembic upgrade head
docker exec f8_backend alembic check  # báo lỗi nếu model lệch migration
```

Sau khi sửa `frontend/package.json`, phải làm mới volume `node_modules`:

```bash
docker compose build frontend
docker compose up -d --force-recreate --renew-anon-volumes frontend
```

---

## Tiến độ

| Phase | Nội dung | Trạng thái |
|---|---|---|
| P0 | Docker Compose, schema DB, migration, seed 34 tỉnh/thành + ngành nghề | ✅ Xong |
| P1 | Auth ứng viên + nhà tuyển dụng, RBAC, guard frontend | ✅ Xong |
| P2 | Tích hợp VietQR, hồ sơ công ty, admin duyệt | ⏳ |
| P3 | CRUD tin tuyển dụng + rich text | ⏳ |
| P4 | Trang công khai: danh sách & chi tiết việc làm | ⏳ |
| P5 | Upload CV lên S3 + ứng tuyển | ⏳ |
| P6 | Nhà tuyển dụng quản lý ứng viên | ⏳ |
| P7 | Job đã lưu, cron hết hạn, SEO | ⏳ |
