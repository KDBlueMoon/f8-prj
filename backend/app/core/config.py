from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """Toàn bộ config đọc từ biến môi trường — không hardcode giá trị nhạy cảm."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = ""
    # DATABASE_URL: str

    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_HOST: str =  ""

    # JWT
    JWT_ALGORITHM: str = "HS256"
    # Access token sống ngắn vì nằm trong bộ nhớ trình duyệt; hết hạn thì
    # dùng refresh token lấy cái mới.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "refresh_token"

    # Danh sách origin cách nhau bởi dấu phẩy, vd "http://localhost:5173,http://127.0.0.1:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    # S3 — dùng từ P5
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-southeast-1"
    S3_BUCKET_NAME: str = ""

    # VietQR — dùng từ P2
    VIETQR_BASE_URL: str = "https://api.vietqr.io/v2"
    # 10 giây, không phải 5. Đo thực tế: VietQR trả kết quả tìm thấy trong
    # ~0,2 giây nhưng mất ~5,3 giây mới trả lời "mã số thuế không tồn tại".
    # Để 5 giây thì mọi mã sai đều bị báo nhầm thành "dịch vụ không phản hồi",
    # người dùng không biết là mình gõ sai mã.
    VIETQR_TIMEOUT_SECONDS: int = 10

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


settings = Settings()  # type: ignore[call-arg]  # DATABASE_URL đến từ biến môi trường
