"""Làm sạch HTML do người dùng soạn trước khi lưu vào database.

Đây là lớp chống XSS chính cho các field `*_html` (mô tả job/công ty): dữ liệu
bẩn lưu vào DB thì mọi nơi hiển thị về sau đều dính, nên phải chặn ngay khi
nhận request, không đợi phía hiển thị tự lo.

Nguyên tắc: **whitelist**, không blacklist.
"""

import re
from html import unescape

import bleach

ALLOWED_TAGS = frozenset({"p", "br", "strong", "b", "em", "i", "u", "h3", "ul", "ol", "li", "a"})

# Cố ý KHÔNG cho `style`, `class`, `id` hay bất kỳ thuộc tính `on*` nào.
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}

# `javascript:` và `data:` bị loại ngay ở đây — đó là hai đường phổ biến nhất để
# nhét mã thực thi vào một thẻ <a> trông vô hại.
ALLOWED_PROTOCOLS = frozenset({"http", "https", "mailto"})

_TAG_PATTERN = re.compile(r"<[^>]*>")
_NON_BREAKING_SPACE = "\xa0"

_SCRIPT_LIKE_BLOCK = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_MAX_STRIP_PASSES = 5


def _drop_script_like_blocks(html: str) -> str:
    for _ in range(_MAX_STRIP_PASSES):
        stripped = _SCRIPT_LIKE_BLOCK.sub("", html)
        if stripped == html:
            break
        html = stripped
    return html


def sanitize_rich_text(html: str) -> str:
    return bleach.clean(
        _drop_script_like_blocks(html),
        tags=set(ALLOWED_TAGS),
        attributes=ALLOWED_ATTRIBUTES,
        protocols=set(ALLOWED_PROTOCOLS),
        strip=True,
    )


def has_visible_text(html: str) -> bool:
    text = unescape(_TAG_PATTERN.sub("", html))
    return bool(text.replace(_NON_BREAKING_SPACE, " ").strip())
