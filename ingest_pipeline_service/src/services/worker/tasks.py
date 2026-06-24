import asyncio
import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .loaders import load_documents
from db.chroma import get_chroma_client
from chromadb import AsyncHttpClient
from db.minio_s3 import s3_client_wrapper
from repositories.minio_repository import MinioRepository
from services.vector_service import VectorService
from services.minio_s3_service import MinioS3Service
from schemas import FileRecordInfo
from settings import settings
from logger import Logger

logger = Logger(__name__)


async def run_ingestion(file_id: int):
    logger.info(f"Начало процесса обработки файла: file_id={file_id}")
    # 1. Получаем через http информацию
    async with httpx.AsyncClient() as client:
        url = f'{settings.file_service_url}/get_file_info'
        logger.debug(f"Запрос метаданных файла {file_id} по адресу: {url}")
        try:
            response = await client.post(
                url=url,
                json={
                    "file_id": file_id
                }
            )
            file_data = response.json()

            logger.info(f"Метаданные файла {file_id} успешно получены: {file_data.get('filename')}")
        except Exception as e:
            logger.error(f"Не удалось получить данные о файле {file_id}: {e}")
            return

    # 2. Скачивание файла
    async with s3_client_wrapper.get_client() as s3_client:

        # инициализация сервисов (DI тут не доступна, поэтому от руки)
        # chroma_client = get_chroma_client()
        chroma_client = await AsyncHttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port
        )
        s3_repo = MinioRepository(s3_client=s3_client, bucket=settings.minio_bucket)
        vector_service = VectorService(chroma_client=chroma_client)
        minio_service = MinioS3Service(s3_repo=s3_repo)

        # получение информации о файле
        tmp_filename = file_data['filename']
        s3_key = file_data['s3_key']
        ext = tmp_filename.split('.')[-1]
        content_type = file_data['content_type']

        # скачивание
        logger.info(f"Скачивание файла {tmp_filename} из S3 (key={s3_key})")
        file_path = await minio_service.save_file_in_tmp(s3_key, tmp_filename)
        logger.debug(f"Файл сохранен локально во временную директорию: {file_path}")

        try:
            logger.info(f"Загрузка и парсинг документа: {tmp_filename}")
            documents = load_documents(file_path, FileRecordInfo(
                id=file_id,
                filename=tmp_filename,
                ext=ext,
                content_type=content_type,
            ))

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
            )
            chunks = splitter.split_documents(documents)
            logger.info(f"Документ разделен на {len(chunks)} частей (чанков)")

            # 5. Сохранение векторов в НАШУ ChromaDB
            logger.info(f"Начало векторизации и сохранения в ChromaDB для файла {file_id}")
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                await vector_service.add_documents(batch)
                logger.debug(f"Обработано чанков: {min(i + batch_size, len(chunks))}/{len(chunks)}")

            logger.info(f"✅ Файл {file_id} ({tmp_filename}) успешно векторизован и сохранен")

        except Exception as e:
            logger.exception(f"Критическая ошибка при обработке файла {file_id}")

        finally:
            logger.debug(f"Удаление временного файла: {file_path}")
            await minio_service.delete_file_from_tmp(file_path)


def ingest_file_by_id(file_id: int):
    """Точка входа для RQ"""
    logger.info(f"Воркер RQ принял задачу на обработку file_id: {file_id}")
    try:
        asyncio.run(run_ingestion(file_id))
    except Exception as e:
        logger.error(f"Ошибка выполнения asyncio задачи: {e}")