from passlib.context import CryptContext

from .repository import get_user_by_username, create_user
from .database import SessionLocal
from .models import User
from utils import Logger


# Контекст шифрования
__context = CryptContext(
    schemes=["bcrypt"],  # Алгоритм шифрования
    deprecated="auto",  # Если пароль будет по старой схеме verify() обновит шифр
)

__logger = Logger("auth")


def authenticate_user(username: str, password: str) -> bool:
    with SessionLocal() as db:
        user: User = get_user_by_username(db, username)

        # Пользователя нет, создаем нового
        if user is None:
            create_user(db=db, username=username, password=__context.hash(password))
            return True

        # Успешная авторизация
        if __context.verify(password, user.password_hash):
            __logger.info(f"User({user.id} - {user.username}) авторизован!")
            return True

        # Неверный пароль
        __logger.info(f"User({user.id} - {user.username}) вводит неверный пароль!")
        return False
