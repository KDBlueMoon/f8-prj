"""Sinh slug thân thiện URL từ chuỗi tiếng Việt."""

import re
import unicodedata

# đ/Đ không tách được dấu bằng NFD nên phải thay riêng.
_D_STROKE = str.maketrans({"đ": "d", "Đ": "d"})
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_length: int = 200) -> str:
    """"Công ty Cổ phần Đầu tư" -> "cong-ty-co-phan-dau-tu"."""
    text = text.translate(_D_STROKE)
    decomposed = unicodedata.normalize("NFD", text)
    ascii_text = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")

    slug = _NON_SLUG_CHARS.sub("-", ascii_text.lower()).strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug


def unique_slug(text: str, suffix: str, max_length: int = 200) -> str:
    """Slug kèm hậu tố ngắn để đảm bảo không trùng, vd "cong-ty-abc-3f9a2b"."""
    base = slugify(text, max_length=max_length - len(suffix) - 1)
    return f"{base}-{suffix}" if base else suffix
