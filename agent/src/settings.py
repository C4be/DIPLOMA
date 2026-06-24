from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SBER_API_KEY: str
    CLOUD_API_KEY: str
    CLOUDRU_API_URL: str
    CONTAINER_LLM: str
    DEBUG: bool = False

    # External services
    RAG_SERVICE_URL: str = "http://rag_service:8000"
    DB_CONNECTOR_URL: str = "http://db_connector_service:8000"

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def rag_retrieval_url(self) -> str:
        return f"{self.RAG_SERVICE_URL}/ask_retrieval"

    @property
    def db_query_url(self) -> str:
        return f"{self.DB_CONNECTOR_URL}/query"

    @property
    def db_schema_url(self) -> str:
        return f"{self.DB_CONNECTOR_URL}/schema"


agent_settings = Settings()
