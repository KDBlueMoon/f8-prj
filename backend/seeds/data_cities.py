"""34 đơn vị hành chính cấp tỉnh, hiệu lực 01/07/2025 (63 -> 34 sau sáp nhập).

id cố định, KHÔNG autoincrement: id 1 = Hà Nội và id 2 = TP.HCM giữ đúng quy ước
city_id trong data.json mẫu, nhờ vậy import dữ liệu mẫu chạy được ngay.
Đổi id của một tỉnh đã phát hành = hỏng dữ liệu job/company đang trỏ tới nó.
"""

# (id, tên, slug, có phải TP trực thuộc Trung ương)
CITIES: list[tuple[int, str, str, bool]] = [
    # 6 thành phố trực thuộc Trung ương
    (1, "Hà Nội", "ha-noi", True),
    (2, "Thành phố Hồ Chí Minh", "ho-chi-minh", True),
    (3, "Hải Phòng", "hai-phong", True),
    (4, "Đà Nẵng", "da-nang", True),
    (5, "Cần Thơ", "can-tho", True),
    (6, "Huế", "hue", True),
    # 28 tỉnh
    (7, "An Giang", "an-giang", False),
    (8, "Bắc Ninh", "bac-ninh", False),
    (9, "Cà Mau", "ca-mau", False),
    (10, "Cao Bằng", "cao-bang", False),
    (11, "Đắk Lắk", "dak-lak", False),
    (12, "Điện Biên", "dien-bien", False),
    (13, "Đồng Nai", "dong-nai", False),
    (14, "Đồng Tháp", "dong-thap", False),
    (15, "Gia Lai", "gia-lai", False),
    (16, "Hà Tĩnh", "ha-tinh", False),
    (17, "Hưng Yên", "hung-yen", False),
    (18, "Khánh Hòa", "khanh-hoa", False),
    (19, "Lai Châu", "lai-chau", False),
    (20, "Lâm Đồng", "lam-dong", False),
    (21, "Lạng Sơn", "lang-son", False),
    (22, "Lào Cai", "lao-cai", False),
    (23, "Nghệ An", "nghe-an", False),
    (24, "Ninh Bình", "ninh-binh", False),
    (25, "Phú Thọ", "phu-tho", False),
    (26, "Quảng Ngãi", "quang-ngai", False),
    (27, "Quảng Ninh", "quang-ninh", False),
    (28, "Quảng Trị", "quang-tri", False),
    (29, "Sơn La", "son-la", False),
    (30, "Tây Ninh", "tay-ninh", False),
    (31, "Thái Nguyên", "thai-nguyen", False),
    (32, "Thanh Hóa", "thanh-hoa", False),
    (33, "Tuyên Quang", "tuyen-quang", False),
    (34, "Vĩnh Long", "vinh-long", False),
]
