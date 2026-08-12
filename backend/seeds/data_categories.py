"""Nhóm ngành và ngành nghề, lấy nguyên từ category_groups trong data.json mẫu.

Lưu ý: group "Lao động phổ thông" trong data.json không có mảng categories.
Vì jobs.category_id là NOT NULL nên seed thêm một ngành mặc định trùng tên
group để tin thuộc nhóm này vẫn gắn được ngành.
"""

# (group_name, group_slug, [(tên ngành, slug ngành), ...])
CATEGORY_GROUPS: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "Kinh doanh / Bán hàng",
        "kinh-doanh-ban-hang",
        [
            ("Sales Xuất nhập khẩu/Logistics", "sales-xuat-nhap-khau-logistics"),
            ("Sales Bất động sản", "sales-bat-dong-san"),
            ("Sales Xây dựng", "sales-xay-dung"),
        ],
    ),
    (
        "Marketing / PR / Quảng cáo",
        "marketing-pr-quang-cao",
        [
            ("Digital Marketing", "digital-marketing"),
            ("Branding & Communications", "branding-communications"),
        ],
    ),
    (
        "Chăm sóc khách hàng (Customer Service) / Vận hành",
        "cham-soc-khach-hang-van-hanh",
        [
            ("Tư vấn & Chăm sóc khách hàng", "tu-van-cham-soc-khach-hang"),
        ],
    ),
    (
        "Nhân sự / Hành chính / Pháp chế",
        "nhan-su-hanh-chinh-phap-che",
        [
            ("Nhân sự & Tuyển dụng", "nhan-su-tuyen-dung"),
        ],
    ),
    (
        "Công nghệ Thông tin",
        "cong-nghe-thong-tin",
        [
            ("Lập trình phần mềm", "lap-trinh-phan-mem"),
        ],
    ),
    (
        "Lao động phổ thông",
        "lao-dong-pho-thong",
        [
            ("Lao động phổ thông", "lao-dong-pho-thong-chung"),
        ],
    ),
]
