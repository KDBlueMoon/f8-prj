"""Unit test cho lớp chống XSS chính (DESIGN mục 6.4).

Test ở đây không đụng database hay HTTP: chỉ kiểm tra đúng hàm làm sạch, vì đó
là nơi duy nhất quyết định thẻ nào được vào DB.
"""

import pytest

from app.utils.sanitize import has_visible_text, sanitize_rich_text


@pytest.mark.parametrize(
    "payload",
    [
        '<script>alert("xss")</script>',
        '<img src=x onerror="alert(1)">',
        '<iframe src="https://evil.example"></iframe>',
        '<svg onload="alert(1)"></svg>',
        "<style>body{display:none}</style>",
    ],
)
def test_dangerous_tags_are_removed(payload: str) -> None:
    cleaned = sanitize_rich_text(f"<p>An toàn</p>{payload}")

    assert "<script" not in cleaned
    assert "<iframe" not in cleaned
    assert "onerror" not in cleaned
    assert "onload" not in cleaned
    assert "<p>An toàn</p>" in cleaned


def test_event_handlers_on_allowed_tags_are_stripped() -> None:
    """Thẻ hợp lệ vẫn có thể mang thuộc tính độc — phải lọc cả thuộc tính."""
    cleaned = sanitize_rich_text('<p onclick="steal()" style="color:red">Nội dung</p>')

    assert cleaned == "<p>Nội dung</p>"


@pytest.mark.parametrize(
    "href",
    ["javascript:alert(1)", "data:text/html;base64,PHNjcmlwdD4=", "vbscript:msgbox(1)"],
)
def test_dangerous_link_protocols_are_dropped(href: str) -> None:
    cleaned = sanitize_rich_text(f'<a href="{href}">Bấm vào đây</a>')

    assert "javascript:" not in cleaned
    assert "data:text/html" not in cleaned
    assert "vbscript:" not in cleaned
    # Chữ vẫn còn, chỉ mất link — người đọc không bị mất nội dung.
    assert "Bấm vào đây" in cleaned


def test_formatting_from_the_editor_toolbar_survives() -> None:
    """Whitelist phải đủ rộng cho đúng những gì toolbar TipTap sinh ra."""
    original = (
        "<h3>Mô tả</h3>"
        "<p><strong>Đậm</strong> <em>nghiêng</em> <u>gạch chân</u></p>"
        "<ul><li>Gạch đầu dòng</li></ul>"
        "<ol><li>Đánh số</li></ol>"
        '<p><a href="https://example.com" title="Trang chủ">Liên kết</a></p>'
    )

    assert sanitize_rich_text(original) == original


def test_script_and_style_bodies_are_removed_entirely() -> None:
    """Không chỉ gỡ thẻ mà bỏ luôn ruột.

    bleach mặc định giữ lại chữ bên trong, nên nội dung dán từ Word (kèm khối
    `<style>` dài) sẽ đổ cả đống CSS vào giữa bài viết.
    """
    cleaned = sanitize_rich_text(
        "<style>.mso{font-size:12pt}</style><p>Nội dung thật</p>"
        '<script type="text/javascript">alert(1)</script>'
    )

    assert cleaned == "<p>Nội dung thật</p>"


def test_nested_script_trick_still_ends_up_harmless() -> None:
    """Mẹo lồng thẻ để né bước dọn — bleach chạy sau vẫn chặn được."""
    cleaned = sanitize_rich_text("<scr<script></script>ipt>alert(1)</script>")

    assert "<script" not in cleaned.lower()


def test_unsupported_tags_keep_their_text() -> None:
    """Dán nội dung từ Word: mất định dạng lạ nhưng không mất chữ."""
    cleaned = sanitize_rich_text("<div><span>Nội dung dán vào</span></div>")

    assert cleaned == "Nội dung dán vào"


@pytest.mark.parametrize("html", ["", "<p></p>", "<p><br></p>", "<p>   </p>", "<p>&nbsp;</p>"])
def test_editor_placeholders_count_as_empty(html: str) -> None:
    """Trình soạn thảo rỗng vẫn gửi lên thẻ, không phải chuỗi rỗng."""
    assert has_visible_text(html) is False


def test_real_content_counts_as_visible() -> None:
    assert has_visible_text("<p><strong>Có chữ</strong></p>") is True
