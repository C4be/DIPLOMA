from fastapi import FastAPI
from contextlib import asynccontextmanager

from db import init_postgres_db, engine
from repositories.minio_repository import MinioRepository
from db import get_s3_client
from routers import get_all_routers
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_postgres_db()

    # Используем DI для получения s3_client
    async for s3_client in get_s3_client():
        s3_repo = MinioRepository(s3_client=s3_client, bucket=settings.minio_bucket)
        await s3_repo.check_or_create_bucket()
        break  # Важно: выходим из async генератора

    yield

    await engine.dispose()


def get_application() -> FastAPI:
    application = FastAPI(
        title="RAG",
        lifespan=lifespan,
        debug=True
    )

    for route in get_all_routers():
        application.include_router(route)

    return application


app = get_application()
