from fastapi import Depends
from redis import Redis
from chromadb import AsyncHttpClient
from typing import Iterator

from db.redis import get_redis_connection
from db.chroma import get_chroma_client
from db.minio_s3 import s3_client_wrapper

from repositories.minio_repository import MinioRepository

from services.queue_service import QueueService
from services.vector_service import VectorService
from services.minio_s3_service import MinioS3Service

from settings import settings


# S3
async def get_s3_client():
    async with s3_client_wrapper.get_client() as client:
        try:
            yield client
        finally:
            pass


# chromadb
async def get_vector_db_client(
    client: AsyncHttpClient = Depends(get_chroma_client)
) -> AsyncHttpClient:
    return client


# queue_service
def get_queue_service(
    redis_conn: Redis = Depends(get_redis_connection)
) -> Iterator[QueueService]:
    try:
        yield QueueService(redis_conn)
    finally:
        redis_conn.close()


# vector_service
async def get_vector_service(
    client: AsyncHttpClient = Depends(get_vector_db_client)
) -> VectorService:
    return VectorService(chroma_client=client)


# minio_repository
async def get_s3_repository(
    s3_client = Depends(get_s3_client)
) -> MinioRepository:
    return MinioRepository(s3_client=s3_client, bucket=settings.minio_bucket)


# minio_service
async def get_minio_s3_service(
    s3_repo: MinioRepository = Depends(get_s3_repository)
) -> MinioS3Service:
    return MinioS3Service(s3_repo)