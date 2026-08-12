from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toàn bộ config đọc từ biến môi trường — không hardcode giá trị nhạy cảm."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = ""
    DATABASE_URL: str

    # Danh sách origin cách nhau bởi dấu phẩy, vd "http://localhost:5173,http://127.0.0.1:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    # S3 — dùng từ P5
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-southeast-1"
    S3_BUCKET_NAME: str = ""

    # VietQR — dùng từ P2
    VIETQR_BASE_URL: str = "https://api.vietqr.io/v2"
    VIETQR_TIMEOUT_SECONDS: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()  # type: ignore[call-arg]  # DATABASE_URL đến từ biến môi trường
