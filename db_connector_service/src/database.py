from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings

engine = create_async_engine(settings.db_url, echo=False, future=True, connect_args={
        "server_settings": {
            "timezone": "Europe/Moscow",  # <--- Задаем таймзону для всех сессий
            "application_name": "fastapi_app" # Заодно удобно для мониторинга
        }
    })
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)