import chromadb
from chromadb.config import Settings
from settings import settings


def get_chroma_client():
    return chromadb.AsyncHttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=Settings(anonymized_telemetry=False)
    )