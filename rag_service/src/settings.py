from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"Database URL: {self.database_url}")

    minio_url: str
    minio_id: str
    minio_pass: str
    minio_region: str
    minio_bucket: str

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    postgres_echo: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()
