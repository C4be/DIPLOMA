import uuid
import httpx
from typing import List
from chromadb import AsyncHttpClient
from langchain_core.documents import Document

from settings import settings

from logger import Logger

logger = Logger(__name__)

class VectorService:
    def __init__(
        self,
        chroma_client: AsyncHttpClient,
        embedding_model_url: str = settings.embedding_model_url,
        timeout: int = 20,
        collection_name: str = settings.chroma_collection_name
    ):
        self.client: AsyncHttpClient = chroma_client
        self.embedding_model_url = embedding_model_url.rstrip("/")
        self.timeout = timeout
        self.collection_name = collection_name
        self._collection = None  # Для ленивой инициализации


    async def _get_collection(self):
        """Асинхронное получение или создание коллекции"""
        if self._collection is None:
            self._collection = await self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection


    async def add_documents(self, batch: List[Document]):
        logger.debug(f"Подготовка {len(batch)} документов для отправки на эмбеддинг")
        # 1. Подготовка данных для эмбеддинг-сервиса
        # payload = {
        #     "documents": [
        #         {"content": doc.page_content, "metadata": doc.metadata}
        #         for doc in batch
        #     ]
        # }

        payload = {
            "texts": [doc.page_content for doc in batch]
        }

        # 2. Получение эмбеддингов
        target_url = f"{self.embedding_model_url}/embed/documents"
        logger.info(f"Запрос эмбеддингов по адресу: {target_url}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=target_url,
                    json=payload,
                )
                # Если статус не 200, это вызовет исключение и попадет в except ниже
                response.raise_for_status()

            result = response.json()
            embeddings = result.get("embeddings")

            if not embeddings:
                logger.error("Сервис вернул пустой список эмбеддингов")
                raise ValueError("Empty embeddings received")

            logger.info(f"Успешно получено {len(embeddings)} векторов")

        except httpx.ConnectError:
            logger.error(f"Сетевая ошибка: Не удалось подключиться к {target_url}. Проверьте доступность сервиса и настройки Docker network.")
            raise RuntimeError(f"Недоступен сервис эмбеддингов по адресу {target_url}")
        except httpx.TimeoutException:
            logger.error(f"Превышен лимит времени ({self.timeout}с) при запросе к {target_url}")
            raise
        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при получении эмбеддингов: {e}")
            raise RuntimeError(f"Embedding service error: {e}")

        # 3. Сохранение в ChromaDB
        logger.debug(f"Сохранение векторов в коллекцию ChromaDB: {self.collection_name}")
        try:
            collection = await self._get_collection()

            documents_content = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            ids = [str(uuid.uuid4()) for _ in range(len(batch))]

            await collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents_content,
                metadatas=metadatas
            )
            logger.info(f"Батч успешно сохранен в ChromaDB. IDs: {ids[0]}...{ids[-1]}")

        except Exception as e:
            logger.exception(f"Ошибка сохранения в ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB storage error: {e}")


    async def search_similar(
        self,
        query: str,
        limit: int = settings.chroma_result_limit
    ) -> List[dict]:
        # 1. Получаем вектор запроса
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=f"{self.embedding_model_url}/embed/query",
                json={"text": query},
            )
            response.raise_for_status()
            query_embedding = response.json().get("embedding")

        # 2. Поиск в ChromaDB (асинхронно)
        collection = await self._get_collection()
        results = await collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )

        # 3. Форматирование
        formatted_results = []
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })

        return formatted_results


    async def clear_database(self):
        """Асинхронное пересоздание коллекции"""
        await self.client.delete_collection(name=self.collection_name)
        self._collection = await self.client.create_collection(name=self.collection_name)