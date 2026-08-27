from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """Toàn bộ config đọc từ biến môi trường — không hardcode giá trị nhạy cảm."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = ""

    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_HOST: str = ""

    JWT_ALGORITHM: str = "HS256"
    # Không có refresh token trong spec hiện tại — access token sống lâu hơn
    # bình thường vì hết hạn là phải đăng nhập lại, không có cách gia hạn.
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    CORS_ORIGINS: str = ""

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """Chết ngay lúc khởi động nếu thiếu SECRET_KEY.

        Nếu để lọt, toàn bộ JWT sẽ được ký bằng chuỗi rỗng và ai cũng giả mạo
        được token — hỏng âm thầm, nguy hiểm hơn nhiều so với việc app không
        khởi động lên.
        """
        if len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY phải có tối thiểu {MIN_SECRET_KEY_LENGTH} ký tự. "
                "Sinh khoá bằng: openssl rand -hex 32"
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()  # type: ignore[call-arg]
