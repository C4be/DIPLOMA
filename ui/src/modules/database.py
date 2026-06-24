from typing import Generator, Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from utils import Logger
from config import settings_db


__logger = Logger("db")
DATABASE_URL = settings_db.get_db_url()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from .models import Base

    __logger.info(f"Синхронное создание БД через engine={engine} ...")
    Base.metadata.create_all(bind=engine)
