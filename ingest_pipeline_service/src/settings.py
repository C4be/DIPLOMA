from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    # === minio_s3 ====
    minio_host: str
    minio_port: str
    minio_id: str
    minio_pass: str
    minio_region: str
    minio_bucket: str

    # === redis ===
    redis_host: str
    redis_port: int
    redis_db: int

    # === file_service_endpoint ===
    file_service_url: str

    # === chroma ===
    chroma_host: str
    chroma_port: int
    chroma_collection_name: str
    chroma_result_limit: int

    embedding_model_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def minio_url(self) -> str:
        return f'http://{self.minio_host}:{self.minio_port}'


settings = Setting()
