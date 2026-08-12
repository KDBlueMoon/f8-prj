"""Làm sạch HTML do người dùng soạn trước khi lưu vào database.

Đây là **lớp chống XSS chính** (DESIGN mục 6.4). Frontend cũng chạy DOMPurify
trước khi render, nhưng đó chỉ là lớp thứ hai: client nào cũng sửa được, còn
dữ liệu bẩn đã vào DB thì mọi nơi hiển thị về sau đều dính — kể cả trang quản
trị hay bản export sau này.

Nguyên tắc: **whitelist**, không blacklist. Chỉ đúng những thẻ mà toolbar TipTap
sinh ra mới được giữ; mọi thứ khác (script, iframe, style, on* handler,
javascript: URL) bị loại bỏ mà không cần liệt kê trước.
"""

import re
from html import unescape

import bleach

# Bám sát toolbar TipTap ở mục 6.4: đậm, nghiêng, gạch chân, H3, danh sách, link.
# `b`/`i` không có trên toolbar nhưng vẫn cho qua vì nội dung dán từ Word/Google
# Docs hay dùng chúng — chặn thì người dùng mất định dạng mà chẳng an toàn thêm.
ALLOWED_TAGS = frozenset(
    {"p", "br", "strong", "b", "em", "i", "u", "h3", "ul", "ol", "li", "a"}
)

# Cố ý KHÔNG cho `style`, `class`, `id` hay bất kỳ thuộc tính `on*` nào.
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}

# `javascript:` và `data:` bị loại ngay ở đây — đó là hai đường phổ biến nhất để
# nhét mã thực thi vào một thẻ <a> trông vô hại.
ALLOWED_PROTOCOLS = frozenset({"http", "https", "mailto"})

MAX_RICH_TEXT_LENGTH = 20_000

_TAG_PATTERN = re.compile(r"<[^>]*>")
_NON_BREAKING_SPACE = "\xa0"

_SCRIPT_LIKE_BLOCK = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_MAX_STRIP_PASSES = 5


def _drop_script_like_blocks(html: str) -> str:
    """Bỏ luôn phần ruột của `<script>` và `<style>`.

    bleach gỡ được hai thẻ này nhưng **giữ lại chữ bên trong** — nội dung dán từ
    Word thường kèm một khối `<style>` dài, để nguyên là đổ cả đống CSS vào giữa
    bài viết. Đây thuần tuý là dọn cho sạch mắt: chốt chặn an toàn vẫn là bleach
    chạy ngay sau đó, nên bước này không cần chống được mọi mẹo né tránh.

    Lặp vài lượt vì gỡ một khối lồng nhau có thể ghép hai mảnh còn lại thành thẻ
    mới (`<scr<script></script>ipt>`).
    """
    for _ in range(_MAX_STRIP_PASSES):
        stripped = _SCRIPT_LIKE_BLOCK.sub("", html)
        if stripped == html:
            break
        html = stripped
    return html


def sanitize_rich_text(html: str) -> str:
    """Trả về HTML chỉ còn các thẻ trong whitelist.

    `strip=True`: thẻ không hợp lệ bị gỡ nhưng phần chữ bên trong được giữ lại.
    Chọn vậy vì người dùng dán nội dung từ nơi khác vào thì mất định dạng còn
    hơn là nhìn thấy `&lt;div&gt;` hiện nguyên xi giữa bài viết.
    """
    return bleach.clean(
        _drop_script_like_blocks(html),
        tags=set(ALLOWED_TAGS),
        attributes=ALLOWED_ATTRIBUTES,
        protocols=set(ALLOWED_PROTOCOLS),
        strip=True,
    )


def has_visible_text(html: str) -> bool:
    """Có chữ thật hay không, sau khi bỏ hết thẻ.

    Trình soạn thảo rỗng vẫn gửi lên `<p></p>` hoặc `<p><br></p>`, nên không thể
    chỉ kiểm tra chuỗi rỗng để biết người dùng đã nhập gì chưa.
    """
    text = unescape(_TAG_PATTERN.sub("", html))
    return bool(text.replace(_NON_BREAKING_SPACE, " ").strip())
