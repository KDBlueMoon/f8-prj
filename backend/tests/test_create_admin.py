import pytest

from seeds.create_admin import _validate_email


class TestValidateEmail:
    def test_accepts_normal_email(self) -> None:
        assert _validate_email("admin@congty.vn") == "admin@congty.vn"

    @pytest.mark.parametrize(
        "email",
        ["admin@f8-topcv.local", "khong-co-a-cong", "admin@", "@congty.vn"],
        ids=["tld-danh-rieng", "thieu-@", "thieu-domain", "thieu-ten"],
    )
    def test_rejects_email_that_login_endpoint_would_refuse(self, email: str) -> None:
        """Script và endpoint đăng nhập phải dùng chung một luật kiểm tra email.

        Trước đây script nhận email domain .local, tạo ra tài khoản admin mà
        endpoint /auth/login từ chối — admin có tài khoản nhưng không đăng nhập
        được, và lỗi chỉ lộ ra lúc thử đăng nhập.
        """
        with pytest.raises(SystemExit):
            _validate_email(email)
