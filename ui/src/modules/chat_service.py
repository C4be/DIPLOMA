import httpx
import gradio as gr
from typing import Sequence

from utils import Logger
from .models import User, Chat
from .database import SessionLocal
from .repository import (
    get_chats_for_user,
    create_chat,
    get_messages_for_chat,
    add_message,
    update_chat_title,
    get_user_by_username,
)


__logger = Logger("chat_service")


def generate_bot_response(user_message: str) -> str:

    # url_rag = f"http://rag_service:8000/ask_retrieval"


    # with httpx.Client(timeout=10.0) as client:
    #     response = client.post(url_rag, json={
    #         "text": user_message
    #     })

    # data = response.json()

    # items = data.get("response", [])
    # blocks = []
    # for el in items:
    #     content = el.get("content", "")
    #     distance = el.get("distance", 0)
    #     metadata = el.get("metadata", {})

    #     # 3. Безопасно достаем путь к файлу.
    #     file_source = metadata.get("file_path") or metadata.get("filename") or "Неизвестный файл"

    #     # Опционально: можно добавить страницу, если она есть
    #     page_info = f", стр. {metadata['page']}" if "page" in metadata else ""

    #     # Формируем красивый блок
    #     block_str = (
    #         f"**Источник:** {file_source}{page_info}\n"
    #         f"**Релевантность:** {distance:.4f}\n"
    #         f"**Текст:**\n{content}"
    #     )
    #     blocks.append(block_str)

    # add_block = "" if not blocks else "\n\n".join(blocks)


    msg = f'Запрос пользователя: {user_message}'
    payload = {"question": msg}
    url_giga = f"http://agent_service:8000/giga"

    __logger.info(f'Пользователь задал сообщение: {msg}')

    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(url_giga, json=payload)

        __logger.info(f'Запрос прошел: {msg}')

        data = response.json()
        return f"#Agent answer:\n{data['answer']}"

    except httpx.RequestError as e:
        return f"Ошибка сети: {e}"


    # try:
    #     with httpx.Client(timeout=10.0) as client:
    #         response = client.get(url)

    #         if response.status_code == 200:
    #             # 1. Парсим JSON ответ
    #             data = response.json()

    #             # 2. Достаем список из ключа "response" (если его нет, вернется пустой список)
    #             items = data.get("response", [])

    #             blocks = []
    #             for el in items:
    #                 content = el.get("content", "")
    #                 distance = el.get("distance", 0)
    #                 metadata = el.get("metadata", {})

    #                 # 3. Безопасно достаем путь к файлу.
    #                 # В твоем примере у PDF это 'file_path', у TXT это 'filename'.
    #                 # Используем .get() и цепочку 'or', чтобы найти хоть что-то.
    #                 file_source = metadata.get("file_path") or metadata.get("filename") or "Неизвестный файл"

    #                 # Опционально: можно добавить страницу, если она есть
    #                 page_info = f", стр. {metadata['page']}" if "page" in metadata else ""

    #                 # Формируем красивый блок
    #                 block_str = (
    #                     f"📄 **Источник:** {file_source}{page_info}\n"
    #                     f"🎯 **Релевантность:** {distance:.4f}\n"
    #                     f"📝 **Текст:**\n{content}"
    #                 )
    #                 blocks.append(block_str)

    #             __logger.info(f'Найдено блоков: {len(blocks)}')

    #             if not blocks:
    #                 return "По вашему запросу ничего не найдено."

    #             return "Самые релевантные ответы:\n\n" + "\n\n---\n\n".join(blocks)

    #         else:
    #             return f"Ошибка API: {response.status_code}: {response.text}"

    # except httpx.RequestError as e:
    #     return f"Ошибка сети: {e}"


def create_new_chat(user_id: int, title: str = "Новый чат"):
    with SessionLocal() as db:
        chat = create_chat(db, user_id)
        update_chat_title(db, chat.id, title)
        chats = get_chats_for_user(db, user_id)
        choices = [(c.title, c.id) for c in chats]
        return choices, chat.id


def load_chat_history(chat_id: int):
    if not chat_id:
        return []
    with SessionLocal() as db:
        messages = get_messages_for_chat(db, chat_id)
        history = []
        for msg in messages:
            history.append({"role": msg.role, "content": msg.content})
        return history


def send_message_and_respond(chat_id: int, user_id: int, message: str, current_history):
    with SessionLocal() as db:
        # 1. Отправка сообщения и получение ответа
        __logger.info(
            f"Пользователь {user_id} отправил сообщение - {message[: min(len(message), 100)]}"
        )
        add_message(db, chat_id, "user", message)
        bot_response = generate_bot_response(message)
        add_message(db, chat_id, "assistant", bot_response)

        # 2. Обновляем заголовок чата, если это первое сообщение
        all_messages = get_messages_for_chat(db, chat_id)
        __logger.info(f"Сообщения: {all_messages}, кол-во: {len(all_messages)}")
        if len(all_messages) == 2:
            new_title = message[:60] + ("..." if len(message) > 60 else "")
            update_chat_title(db, chat_id, new_title)
            chats = get_chats_for_user(db, user_id)
            choices = [(c.title, c.id) for c in chats]
            __logger.info(f"Нужный чат: {chat_id}. Выборы: {choices}")
            dropdown_update = gr.update(choices=choices, value=chat_id)
        else:
            dropdown_update = gr.update()

        new_history = current_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": bot_response},
        ]
        return new_history, dropdown_update


def get_user_and_load_chats(username: str):
    with SessionLocal() as db:
        user: User = get_user_by_username(db, username)
        chats: Sequence[Chat] = get_chats_for_user(db, user.id)

        __logger.info(
            f"Загружен пользователь {user.username} и его чаты {chats if chats else []}"
        )
        # return user.id, chats if chats else []
        return user.id, [(c.title, c.id) for c in chats] if chats else []


def save_files(user_id, chat_id, files) -> list[str]:
    __logger.info(f"Файл {files} сохранен {user_id} с чата {chat_id}")
    return [f"form_user_{files}"]


def get_chat_files(chat_id):
    return ["1.pdf", "2.pdf"]


def get_file_path(user_id, chat_id, filename):
    return gr.File()
