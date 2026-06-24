from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncAttrs
)
from sqlalchemy.orm import DeclarativeBase
from settings import settings


# Асинхронный движок
engine = create_async_engine(
    settings.database_url,
    echo=settings.postgres_echo,
)


# Фабрика сессий
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False
)


class Base(AsyncAttrs, DeclarativeBase):
    """ Базовый класс для всех моделей """
    pass


async def get_session():
    """ DI зависимость для FastAPI (в роутах: db: AsyncSession = Depends(get_session)) """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_postgres_db():
    """ Начальная инициализация таблиц """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
