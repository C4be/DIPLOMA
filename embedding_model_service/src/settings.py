from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    embedding_model: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Setting()
