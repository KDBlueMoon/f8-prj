import uuid

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.utils.slug import slugify, unique_slug


class TestPasswordHashing:
    def test_hash_is_not_the_plain_password(self) -> None:
        password = "MatKhau123"

        assert hash_password(password) != password

    def test_same_password_hashes_differently_each_time(self) -> None:
        """Mỗi lần băm dùng salt mới nên hai người cùng mật khẩu vẫn khác hash."""
        assert hash_password("MatKhau123") != hash_password("MatKhau123")

    def test_verify_accepts_correct_password(self) -> None:
        assert verify_password("MatKhau123", hash_password("MatKhau123"))

    def test_verify_rejects_wrong_password(self) -> None:
        assert not verify_password("SaiMatKhau1", hash_password("MatKhau123"))

    def test_verify_returns_false_for_corrupt_hash(self) -> None:
        """Hash hỏng trong DB không được làm request chết thành lỗi 500."""
        assert not verify_password("MatKhau123", "khong-phai-hash-bcrypt")

    @pytest.mark.parametrize(
        "password",
        [
            "Mật khẩu tiếng Việt có dấu 2026",
            "a" * 200,
            "Mật khẩu rất dài của người dùng Việt Nam 2026" * 3,
        ],
        ids=["tieng-viet", "200-ky-tu", "vuot-72-byte"],
    )
    def test_long_passwords_are_not_truncated(self, password: str) -> None:
        """bcrypt chỉ nhận 72 byte; phải băm trước để không bị cắt cụt âm thầm."""
        password_hash = hash_password(password)

        assert verify_password(password, password_hash)
        # Nếu bị cắt ở 72 byte thì hai chuỗi khác nhau phần đuôi vẫn khớp nhau.
        assert not verify_password(password + "them-duoi", password_hash)


class TestJwt:
    def test_access_token_carries_user_id_and_role(self) -> None:
        user_id = uuid.uuid4()

        payload = decode_token(create_access_token(user_id, "CANDIDATE"), "access")

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "CANDIDATE"

    def test_access_token_is_not_accepted_as_refresh(self) -> None:
        token = create_access_token(uuid.uuid4(), "CANDIDATE")

        assert decode_token(token, "refresh") is None

    def test_refresh_token_is_not_accepted_as_access(self) -> None:
        token, _, _ = create_refresh_token(uuid.uuid4())

        assert decode_token(token, "access") is None

    def test_refresh_token_has_unique_jti_each_time(self) -> None:
        """jti là thứ dùng để thu hồi token, trùng nhau là logout sai người."""
        _, first_jti, _ = create_refresh_token(uuid.uuid4())
        _, second_jti, _ = create_refresh_token(uuid.uuid4())

        assert first_jti != second_jti

    def test_tampered_token_is_rejected(self) -> None:
        token = create_access_token(uuid.uuid4(), "CANDIDATE")
        tampered = token[:-4] + ("aaaa" if token[-4:] != "aaaa" else "bbbb")

        assert decode_token(tampered, "access") is None

    def test_garbage_token_is_rejected(self) -> None:
        assert decode_token("khong-phai-jwt", "access") is None


class TestSlugify:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Công ty Cổ phần Đầu tư", "cong-ty-co-phan-dau-tu"),
            ("Đắk Lắk", "dak-lak"),
            ("Thành phố Hồ Chí Minh", "thanh-pho-ho-chi-minh"),
            ("Senior Frontend Developer (ReactJS / Next.js)", "senior-frontend-developer-reactjs-next-js"),
            ("  nhiều   khoảng   trắng  ", "nhieu-khoang-trang"),
        ],
    )
    def test_converts_vietnamese_to_ascii_slug(self, text: str, expected: str) -> None:
        assert slugify(text) == expected

    def test_handles_text_without_any_usable_character(self) -> None:
        assert slugify("!!!???") == ""

    def test_truncates_without_leaving_a_cut_word(self) -> None:
        result = slugify("cong ty co phan dau tu phat trien", max_length=20)

        assert len(result) <= 20
        assert not result.endswith("-")
        assert "dau" not in result.split("-")[-1] or result.split("-")[-1] == "dau"

    def test_unique_slug_appends_suffix(self) -> None:
        assert unique_slug("Công ty ABC", suffix="3f9a2b") == "cong-ty-abc-3f9a2b"

    def test_unique_slug_falls_back_to_suffix_when_name_has_no_ascii(self) -> None:
        assert unique_slug("!!!", suffix="3f9a2b") == "3f9a2b"
