import chromadb
import uuid
import httpx
from typing import List
from chromadb.config import Settings
from langchain_core.documents import Document
from typing import List

from settings import settings


class VectorService:

    def __init__(
        self,
        embedding_model_url: str = settings.embedding_model_url,
        timeout: int = 10,
        collection_name: str = settings.chroma_collection_name
    ):
        self.embedding_model_url = embedding_model_url.rstrip("/")
        self.timeout = timeout

        # Создаем клиента для подключения к CHROMA_DB
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # метрика: косинусное сходство
        )

    async def search_similar(
        self,
        query: str,
        limit: int = settings.chroma_result_limit
    ) -> List[dict]:
        """Поиск похожих кусочков текста по запросу пользователя через внешний сервис"""

        # 1. Готовим payload согласно твоей схеме QueryRequest
        payload = {"text": query}

        # 2. Делаем запрос в embedding сервис на эндпоинт /query
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=f"{self.embedding_model_url}/embed/query", # Убедись, что путь верный
                    json=payload,
                )
                response.raise_for_status()

                # Извлекаем вектор из ответа (согласно QueryResponse)
                data = response.json()
                query_embedding = data.get("embedding")

                if not query_embedding:
                    raise RuntimeError("Service response missing 'embedding' field")

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Vector service error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Connection to vector service failed: {e}")

        # 3. Выполняем поиск в ChromaDB, используя полученный вектор
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )

        # 4. Форматируем вывод
        formatted_results = []
        # Chroma возвращает списки списков, берем первый элемент [0]
        if results and results['ids']:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })

        return formatted_results


    # async def clear_database(self):
    #     """Пересоздание коллекции"""
    #     self.client.delete_collection(name=self.collection_name)
    #     self.collection = self.client.create_collection(name=self.collection_name)

