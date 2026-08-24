# Hướng dẫn dùng API — Frontend

Tài liệu này dành cho người code phần frontend: khi nào gọi API nào, cần đăng
nhập/role gì, request/response ra sao, và cách xử lý lỗi. Xem thêm thiết kế
đầy đủ ở [`docs/DESIGN.md`](../docs/DESIGN.md) nếu cần hiểu lý do đằng sau một
quyết định (invariant, tại sao một trường bị ẩn khỏi response...).

- **Base URL:** biến môi trường `VITE_API_BASE_URL` (mặc định
  `http://localhost:8000/api/v1`).
- **Swagger UI (dev):** http://localhost:8000/docs — dùng để thử API trực
  tiếp, xem đúng schema mới nhất khi tài liệu này lỗi thời.
- **Helper có sẵn:** `src/lib/apiClient.ts` export `apiGet`, `apiPost`,
  `apiPatch`, `apiDelete`, `buildQuery`. Dùng các hàm này thay vì gọi `fetch`
  thẳng — chúng tự đính kèm access token, tự refresh token khi hết hạn 401, và
  tự parse lỗi thành `ApiError`.

```ts
import { apiGet, apiPost, buildQuery } from '@/lib/apiClient'

const jobs = await apiGet(`/jobs${buildQuery({ q: 'python', page: 1 })}`)
const created = await apiPost('/employer/jobs', payload)
```

---

## 1. Xác thực & phân quyền

4 role: `GUEST` (chưa đăng nhập, không có bản ghi user), `CANDIDATE`,
`EMPLOYER`, `ADMIN`.

- **Access token**: sống 15 phút, nằm trong response body, FE giữ **trong bộ
  nhớ** (`stores/authStore.ts`, Zustand) — **không** lưu `localStorage`.
- **Refresh token**: sống 7 ngày, nằm trong httpOnly cookie do backend set —
  JS không đọc được. Mọi request phải gửi kèm `credentials: 'include'`
  (`apiClient.ts` đã tự làm việc này).
- Khi access token hết hạn (401), `apiClient.ts` tự gọi `POST /auth/refresh`
  một lần rồi thử lại request gốc — component không cần tự xử lý việc này.
- Route công khai (không cần login): trang chủ, danh sách/chi tiết job, danh
  sách/chi tiết công ty, đăng nhập/đăng ký. Các route còn lại bọc bởi
  `<ProtectedRoute allow={[...]} />` (xem `App.tsx`) — **đây chỉ là UX**, thực
  sự chặn quyền là ở backend.

### `POST /auth/register/candidate` — Đăng ký ứng viên
Public. Đăng ký xong đăng nhập luôn.

```json
// Request
{ "email": "ung.vien@example.com", "password": "MatKhau123", "full_name": "Nguyễn Văn A", "phone_number": "0901234567" }
```
→ trả `LoginResponse` (xem mục 1.4).

### `POST /auth/register/employer` — Đăng ký nhà tuyển dụng + hồ sơ công ty
Public. Tạo `user(role=EMPLOYER)` + `company(status=PENDING)` trong 1
transaction, đăng nhập luôn. Company `PENDING` thì login được nhưng **chưa
đăng tin được** (nhận lỗi `COMPANY_NOT_APPROVED` cho tới khi admin duyệt).

```json
// Request
{
  "email": "hr@congty.vn",
  "password": "MatKhau123",
  "full_name": "Nguyễn Văn A",
  "phone_number": "0901234567",
  "company": {
    "tax_code": "0316794479",
    "company_name": "CÔNG TY TNHH CASSO",
    "international_name": "CASSO COMPANY LIMITED",
    "short_name": "CASSO",
    "director": "Nguyễn Kiểm Thử",
    "headquarters_address": "1 Đường ABC, Hà Nội",
    "email": "contact@casso.vn",
    "phone_number": "0281234567",
    "company_size": "10-24",
    "website": "https://casso.vn",
    "issued_date": "2020-01-01",
    "category_group_id": null
  }
}
```
Gợi ý UX: gọi `GET /companies/lookup-tax-code/{mst}` trước để tự điền 4
trường (`company_name`, `international_name`, `short_name`,
`headquarters_address`); các trường còn lại luôn phải nhập tay (VietQR không
trả về).

### `POST /auth/login`

```json
{ "email": "user@example.com", "password": "MatKhau123" }
```

### `POST /auth/refresh`
Không cần body — đọc refresh token từ cookie. FE thường **không** tự gọi trực
tiếp, để `apiClient.ts` tự xử lý khi gặp 401. Có dùng riêng lúc khởi động app
để khôi phục phiên đăng nhập sau khi F5 (`useSessionBootstrap.ts`).

### `POST /auth/logout`
Cần đăng nhập. Không có body, trả `204 No Content`.

### `GET /auth/me`
Cần đăng nhập. Trả user hiện tại + company (nếu là EMPLOYER).

### 1.4 Response chung — `LoginResponse`
Trả về bởi `register/*`, `login`, `refresh`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid", "email": "...", "role": "EMPLOYER",
    "full_name": "...", "phone_number": "...", "avatar_url": null
  },
  "company": {
    "id": "uuid", "company_name": "...", "short_name": "...", "slug": "...",
    "logo_url": null, "status": "PENDING", "verification_tier": "UNVERIFIED",
    "rejected_reason": null
  }
}
```
`company` là `null` với CANDIDATE/ADMIN.

---

## 2. Danh mục (public, không cần login)

| Method | Path | Dùng khi nào |
|---|---|---|
| GET | `/cities` | Đổ dropdown chọn tỉnh/thành (34 bản ghi, 6 thành phố trực thuộc TW xếp trước) |
| GET | `/categories` | Đổ dropdown ngành nghề, dạng cây `[{ id, group_name, group_slug, categories: [{ id, name, slug }] }]` |

Dữ liệu gần như tĩnh — nên cache lâu ở tầng TanStack Query (`staleTime` cao).

---

## 3. Việc làm & công ty — trang công khai (không cần login)

### `GET /jobs` — danh sách job kèm filter
Query params (tất cả optional trừ phân trang có default):
`q`, `category_id`, `group_id`, `city_id`, `job_type`, `experience_level`,
`salary_min`, `salary_max`, `is_hot`, `sort` (`newest` | `salary_desc` |
`deadline`, mặc định `newest`), `page` (mặc định 1), `page_size` (mặc định
20, tối đa 50).

```
GET /jobs?q=python&city_id=1&job_type=FULL_TIME&sort=salary_desc&page=1
```

Response — mọi endpoint list đều bọc theo dạng này:
```json
{
  "items": [ { "id": "...", "title": "...", "slug": "...", "company": { "id": "...", "company_name": "...", "logo_url": null, "verification_tier": "VERIFIED" }, "locations": [...], ... } ],
  "meta": { "page": 1, "page_size": 20, "total": 137, "total_pages": 7 }
}
```
Lưu ý: `salary_min`/`salary_max` là `null` khi job ghi "Thoả thuận" (`salary_type: "AGREEMENT"`) — không tự suy diễn ra 0.

### `GET /jobs/{slug}` — chi tiết job
Trả full nội dung (`description_html`, `requirements_html`, `benefits_html`
— **đã sanitize ở backend, vẫn phải chạy qua `<SafeHtml>` ở FE trước khi
render**, đừng `dangerouslySetInnerHTML` trực tiếp) kèm object `company` đầy
đủ lồng vào. `company` ở đây **không có** `email`/`phone_number`/`director` —
liên hệ nhà tuyển dụng chỉ qua chức năng ứng tuyển.

### `GET /companies` — danh sách công ty đã duyệt
Query: `q`, `group_id`, `page`, `page_size`. Mỗi item có thêm `open_job_count`
(số tin đang tuyển).

### `GET /companies/{slug}` — trang công ty
Trả hồ sơ công ty + `open_jobs` (tối đa 50 tin đang tuyển) trong cùng 1
response — không cần gọi 2 lần.

### `GET /companies/lookup-tax-code/{tax_code}`
Public, dùng trong form đăng ký NTD để tự điền form theo MST. `tax_code`:
10 hoặc 13 chữ số.

- `200`: `{ tax_code, company_name, international_name, short_name, headquarters_address }`.
- `404 TAX_CODE_NOT_FOUND`: MST không tồn tại — để user tự sửa lại, đừng chặn submit.
- `503 TAX_LOOKUP_UNAVAILABLE`: VietQR không phản hồi — **không chặn đăng
  ký**, hiện thông báo "không tra cứu được, vui lòng nhập tay" và để mọi ô
  trống cho nhập tay.

---

## 4. Employer (`role=EMPLOYER`, cần `Authorization: Bearer <token>`)

Toàn bộ nhóm này backend tự suy ra công ty từ token — **không** truyền
`company_id` từ client.

| Method | Path | Mô tả |
|---|---|---|
| GET | `/employer/company` | Hồ sơ công ty mình |
| PATCH | `/employer/company` | Sửa hồ sơ (không sửa được `tax_code`) |
| POST | `/employer/company/addresses` | Thêm địa chỉ VP |
| DELETE | `/employer/company/addresses/{id}` | Xoá địa chỉ VP |
| GET | `/employer/jobs` | Tin của mình, mọi trạng thái. Query: `status`, `q`, `page`, `page_size` |
| GET | `/employer/jobs/counts` | `{ "DRAFT": 2, "PUBLISHED": 5, ... }` — hiện badge số lượng theo tab |
| GET | `/employer/jobs/{id}` | Chi tiết 1 tin của mình |
| POST | `/employer/jobs` | Tạo tin mới, `status` chỉ nhận `DRAFT` hoặc `PUBLISHED` |
| PATCH | `/employer/jobs/{id}` | Sửa nội dung tin (không sửa `status`, không sửa `slug`) |
| PATCH | `/employer/jobs/{id}/status` | Đổi trạng thái, chỉ nhận `PUBLISHED` hoặc `CLOSED` |
| DELETE | `/employer/jobs/{id}` | Xoá (soft delete) |

Ví dụ tạo tin:
```json
// POST /employer/jobs
{
  "title": "Lập trình viên Backend Python",
  "category_id": "uuid",
  "job_type": "FULL_TIME",
  "experience_level": "1_2",
  "quantity": 2,
  "salary_type": "RANGE",
  "salary_min": 20000000,
  "salary_max": 35000000,
  "deadline": "2026-12-31T00:00:00Z",
  "description_html": "<p>Mô tả công việc</p>",
  "requirements_html": "<p>Yêu cầu ứng viên</p>",
  "benefits_html": "<p>Quyền lợi</p>",
  "locations": [{ "city_id": 1, "address_detail": "47 Nguyễn Tuân" }],
  "status": "PUBLISHED"
}
```
- Gửi `status: "PUBLISHED"` khi công ty chưa `APPROVED` → lỗi
  `COMPANY_NOT_APPROVED` (không âm thầm lưu thành `DRAFT`) — form phải hiện rõ
  lỗi này, không được nuốt.
- `description_html`/`requirements_html`/`benefits_html` đi qua
  `RichTextEditor` (TipTap) — chỉ bật đúng các nút: bold, italic, underline,
  H3, bullet/ordered list, link, undo/redo. Các tính năng khác của
  `StarterKit` (strike, code, blockquote...) phải tắt vì backend sẽ strip khi
  sanitize, bật lên rồi mất là NTD tưởng bug.
- `deadline` phải là thời điểm tương lai, gửi ISO 8601 (có timezone).

---

## 5. Admin (`role=ADMIN`, cần token)

| Method | Path | Mô tả |
|---|---|---|
| GET | `/admin/companies` | Hàng đợi hồ sơ công ty. Query: `status`, `q`, `page`, `page_size` |
| GET | `/admin/companies/counts` | Số hồ sơ theo từng trạng thái (badge tab) |
| GET | `/admin/companies/{id}` | Chi tiết 1 hồ sơ |
| PATCH | `/admin/companies/{id}/status` | `{ "status": "APPROVED" }` hoặc `{ "status": "REJECTED", "rejected_reason": "..." }` — bắt buộc lý do khi từ chối |
| PATCH | `/admin/companies/{id}/verification` | `{ "verification_tier": "VERIFIED" }` — gắn/gỡ badge "Đã xác thực" |
| GET | `/admin/jobs` | Toàn bộ tin mọi công ty (không phải hàng đợi duyệt — tin không cần duyệt). Query: `status`, `q`, `company_id`, `page`, `page_size` |
| GET | `/admin/jobs/{id}` | Chi tiết 1 tin |
| PATCH | `/admin/jobs/{id}/takedown` | `{ "takedown_reason": "..." }` — gỡ tin vi phạm, lý do bắt buộc (min 5 ký tự) |
| PATCH | `/admin/jobs/{id}/hot` | `{ "is_hot": true }` |
| GET | `/admin/users` | Danh sách user. Query: `q`, `page`, `page_size` |
| PATCH | `/admin/users/{id}/status` | `{ "is_active": false }` — khoá/mở tài khoản |

---

## 6. Xử lý lỗi

Mọi lỗi nghiệp vụ trả cùng 1 shape:
```json
{ "detail": { "code": "COMPANY_NOT_APPROVED", "message": "Công ty chưa được duyệt, chưa thể đăng tin." } }
```
`apiClient.ts` đã parse sẵn thành `ApiError { code, message, status, fieldErrors? }`
— bắt bằng `try/catch` và so theo `error.code`, đừng so theo `error.message`
(message chỉ để hiển thị, có thể đổi câu chữ). Lỗi validate 422 của FastAPI có
shape khác (mảng theo field) — `apiClient.ts` cũng tự gom vào `fieldErrors`
(key dạng `"company.tax_code"`) để gán thẳng vào `setError` của React Hook
Form.

Mã lỗi hay gặp theo nhóm:

| Nhóm | Code | HTTP | Ý nghĩa |
|---|---|---|---|
| Auth | `EMAIL_TAKEN` | 409 | Email đã đăng ký |
| Auth | `INVALID_CREDENTIALS` | 401 | Sai email/mật khẩu (dùng chung 1 thông báo, không lộ email tồn tại hay không) |
| Auth | `NOT_AUTHENTICATED` | 401 | Thiếu/sai access token |
| Auth | `ACCOUNT_DISABLED` | 403 | Tài khoản bị admin khoá |
| Auth | `FORBIDDEN_ROLE` | 403 | Đúng role yêu cầu login nhưng sai role (VD: CANDIDATE gọi endpoint EMPLOYER) |
| Auth | `INVALID_REFRESH_TOKEN` | 401 | Refresh token hết hạn/đã thu hồi — điều hướng về `/dang-nhap` |
| Company | `TAX_CODE_TAKEN` | 409 | MST đã có công ty đăng ký |
| Company | `TAX_CODE_NOT_FOUND` | 404 | Tra cứu VietQR không tìm thấy MST |
| Company | `TAX_LOOKUP_UNAVAILABLE` | 503 | VietQR không phản hồi — không chặn đăng ký |
| Job | `COMPANY_NOT_APPROVED` | 403 | Công ty chưa duyệt, không đăng tin `PUBLISHED` được |
| Validate | `VALIDATION_ERROR` | 422 | Sai định dạng field — đọc `fieldErrors` |

---

## 7. State & quy ước dùng chung ở FE

- **Server state**: TanStack Query — query key nên theo path + params, VD
  `['jobs', filters]`.
- **Filter job**: đưa vào URL search params (`useJobFilters.ts`) chứ không
  giữ trong state riêng — để share link, back/forward, F5 hoạt động đúng.
- **Auth state**: `useAuthStore` (Zustand) — đọc `status` (`'checking' |
  'authenticated' | 'guest'`) trước khi quyết định render, tránh nháy UI sai
  role lúc app vừa load xong đang chờ `useSessionBootstrap` gọi `/auth/refresh`.
- **HTML từ rich text** (mô tả job, mô tả công ty): luôn qua `<SafeHtml>`,
  không tự `dangerouslySetInnerHTML`.
