import gradio as gr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingLogger(BaseSettings):
    log_is_use: bool
    log_level: str
    log_path: str
    log_into_file: str

    model_config = SettingsConfigDict(
        env_file="config.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings_logger = SettingLogger()
