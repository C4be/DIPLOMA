from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
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

settings = Setting()
