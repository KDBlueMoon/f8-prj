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
limiter = Limiter(key_func=get_remote_address)
