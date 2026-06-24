from sqlalchemy import select, update
from sqlalchemy.orm import Session
from typing import Optional, Sequence

from .models import User, Chat, Message


# ============================================================
# Обработка пользователя
# ============================================================


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.execute(select(User).filter_by(username=username)).scalar_one_or_none()


def create_user(db: Session, username: str, password: str) -> User:
    user = User(username=username, password_hash=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# Обработка Чатов
# ============================================================


def get_chats_for_user(db: Session, user_id: int) -> Sequence[Chat]:
    return (
        db.execute(
            select(Chat).filter_by(user_id=user_id).order_by(Chat.created_at.desc())
        )
        .scalars()
        .all()
    )


def create_chat(db: Session, user_id: int) -> Chat:
    chat = Chat(user_id=user_id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def update_chat_title(db: Session, chat_id: int, title: str):
    db.execute(update(Chat).where(Chat.id == chat_id).values(title=title))
    db.commit()


# ============================================================
# Обработка Сообщений
# ============================================================


def get_messages_for_chat(db: Session, chat_id: int) -> Sequence[Message]:
    return (
        db.execute(
            select(Message).filter_by(chat_id=chat_id).order_by(Message.timestamp)
        )
        .scalars()
        .all()
    )


def add_message(db: Session, chat_id: int, role: str, content: str) -> Message:
    message = Message(chat_id=chat_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
