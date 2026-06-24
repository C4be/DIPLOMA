import gradio as gr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsDB(BaseSettings):
    db_driver: str
    db_user: str
    db_pass: str
    db_host: str
    db_port: str
    db_name: str

    model_config = SettingsConfigDict(
        env_file="config.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    def get_db_url(self):
        # postgresql+psycopg2://admin:admin@localhost:5432/questions_answers
        return f"{self.db_driver}://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"


settings_db = SettingsDB()
