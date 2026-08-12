"""Giới hạn tần suất gọi cho các endpoint dễ bị dò quét.

Bộ đếm nằm trong bộ nhớ tiến trình: đủ cho một instance, nhưng khi chạy nhiều
worker/instance thì mỗi tiến trình đếm riêng nên hạn mức thực tế nhân lên theo
số tiến trình. Muốn siết chặt ở production thì chuyển sang storage Redis.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Lưu ý: get_remote_address lấy IP kết nối trực tiếp. Khi đặt sau reverse proxy
# phải cấu hình proxy chuyển tiếp IP thật, nếu không mọi request sẽ tính chung
# vào IP của proxy.
#
# key_style="endpoint" là bắt buộc, không phải tuỳ chọn. Mặc định của slowapi là
# "url" — đếm theo URL cụ thể, nên với route có tham số như
# /companies/lookup-tax-code/{tax_code} thì mỗi mã số thuế là một bộ đếm riêng
# và hạn mức không bao giờ chạm tới. Kẻ quét dữ liệu chỉ cần đổi tham số là
# vượt qua. "endpoint" đếm theo route, đúng ý đồ.
limiter = Limiter(key_func=get_remote_address, key_style="endpoint")
