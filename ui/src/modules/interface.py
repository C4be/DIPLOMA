import os
import gradio as gr
import asyncio, httpx
from utils import Logger
from .auth import authenticate_user
from .chat_service import (
    create_new_chat,
    load_chat_history,
    send_message_and_respond,
    get_user_and_load_chats,
    save_files,
    get_chat_files,
    get_file_path,
)


__logger = Logger("interface")


with gr.Blocks(title="# Помощник по хранилищу") as demo:
    current_user = gr.State(None)  # user_id
    current_chat = gr.State(None)  # chat_id
    files_visible = gr.State(False)

    with gr.Column(visible=True, elem_id="login_column") as login_column:
        gr.Markdown("## 🔐 Вход в систему")
        username = gr.Textbox(label="Логин")
        password = gr.Textbox(label="Пароль", type="password")
        login_error = gr.Markdown(visible=False, elem_id="error_msg")
        login_btn = gr.Button("Войти")

    # === Интерфейс ===
    with gr.Column(visible=False, elem_id="main_column") as main_column:
        with gr.Row(elem_id="header"):
            files_btn = gr.Button("Показать файлы")
            logout_btn = gr.Button("Выйти")

        with gr.Row(elem_id="chat_window"):
            with gr.Column(scale=1, elem_id="chats"):
                new_chat_btn = gr.Button("> Новый чат <")
                chats_dropdown = gr.Dropdown(
                    label="История чатов",
                    choices=[],
                    value=None,
                    interactive=True,
                    elem_id="chats_dropdown",
                )

            with gr.Column(scale=4, elem_id="current_chat"):
                chatbot = gr.Chatbot(
                    label="Чат", height=600, buttons=["copy", "copy_all"]
                )
                msg_input = gr.Textbox(
                    label="Сообщение", placeholder="Введите текст...", lines=2
                )
                send_btn = gr.Button("Отправить")

            with gr.Column(scale=1, elem_id="files", visible=False) as files_column:
                gr.Markdown("### 📁 Файлы чата")

                upload_files = gr.File(
                    label="Загрузить файлы", file_count="multiple", interactive=True
                )

                files_dropdown = gr.Dropdown(
                    label="Доступные файлы", choices=[], interactive=True
                )

                download_file = gr.File(label="Скачать файл", interactive=False)

    def login(username, password):
        if not username or not password:
            __logger.warning(f"Пользователь {username} ввел пустые поля!")
            return (
                gr.update(value=None),  # current_user
                gr.update(elem_id="chats_dropdown", value=None),  # chats_dropdown
                gr.update(
                    elem_id="login_column", visible=True
                ),  # login_column показать
                gr.update(elem_id="main_column", visible=False),  # main_column скрыть
                gr.update(
                    elem_id="error_msg", visible=True, value="Введите логин и пароль"
                ),  # сообщение с ошибкой
            )

        try:
            if not authenticate_user(username, password):
                raise ValueError(f"Неверный пароль для пользователя")

            user_id, choices = get_user_and_load_chats(username)
            __logger.info(
                f"Пользователь {username} успешно зашел в приложение и имеет чаты: {choices}"
            )
            return (
                user_id,  # current_user
                gr.update(elem_id="chats_dropdown", choices=choices),  # chats_dropdown
                gr.update(elem_id="login_column", visible=False),  # login_column скрыть
                gr.update(elem_id="main_column", visible=True),  # main_column показать
                gr.update(
                    elem_id="error_msg", visible=False, value=""
                ),  # очищаем ошибку
            )

        except ValueError as e:
            __logger.warning(f"Пользователь {username} ввел неверный пароль!")
            return (
                gr.update(value=None),  # current_user
                gr.update(elem_id="chats_dropdown", value=None),  # chats_dropdown
                gr.update(
                    elem_id="login_column", visible=True
                ),  # login_column показать
                gr.update(elem_id="main_column", visible=False),  # main_column скрыть
                gr.update(
                    elem_id="error_msg", visible=True, value=str(e)
                ),  # сообщение из обработчика ошибок
            )

    login_btn.click(
        login,
        inputs=[username, password],
        outputs=[current_user, chats_dropdown, login_column, main_column, login_error],
    )

    def new_chat(user_id):
        __logger.info(f"Пользователь {user_id} создал новый чат!")
        choices, new_chat_id = create_new_chat(user_id)
        return (
            gr.update(choices=choices, value=new_chat_id),
            new_chat_id,
            [],  # очистить чат
        )

    new_chat_btn.click(
        new_chat, inputs=current_user, outputs=[chats_dropdown, current_chat, chatbot]
    )

    def load_chat_files(chat_id):
        if not chat_id:
            __logger.warning("Передан пустой чат")
            return gr.update(choices=[])

        files = get_chat_files(chat_id)
        return gr.update(choices=files)

    chats_dropdown.change(
        load_chat_history, inputs=chats_dropdown, outputs=chatbot
    ).then(lambda x: x, inputs=chats_dropdown, outputs=current_chat).then(
        load_chat_files, inputs=current_chat, outputs=files_dropdown
    )

    # def send(msg, history, chat_id, user_id):
    #     if not msg.strip() or not chat_id:
    #         return history, "", gr.update()

    #     new_history, dropdown_update = send_message_and_respond(chat_id, user_id, msg, history)
    #     return new_history, "", dropdown_update

    # send_btn.click(
    #     send,
    #     inputs=[msg_input, chatbot, current_chat, current_user],
    #     outputs=[chatbot, msg_input, chats_dropdown]
    # )

    # msg_input.submit(
    #     send,
    #     inputs=[msg_input, chatbot, current_chat, current_user],
    #     outputs=[chatbot, msg_input, chats_dropdown]
    # )

    def send(msg, history, chat_id, user_id):
        if not msg.strip() or not user_id:
            return history, "", gr.update(), chat_id

        # 🔹 ЕСЛИ ЧАТА ЕЩЁ НЕТ — СОЗДАЁМ
        if not chat_id:
            choices, new_chat_id = create_new_chat(user_id, msg[: min(len(msg), 60)])
            chat_id = new_chat_id
            dropdown_update = gr.update(choices=choices, value=new_chat_id)
            history = []  # новый чат — пустая история
            new_history, _ = send_message_and_respond(chat_id, user_id, msg, history)
        else:
            new_history, dropdown_update = send_message_and_respond(
                chat_id, user_id, msg, history
            )

        return new_history, "", dropdown_update, chat_id

    send_btn.click(
        send,
        inputs=[msg_input, chatbot, current_chat, current_user],
        outputs=[chatbot, msg_input, chats_dropdown, current_chat],
    )

    msg_input.submit(
        send,
        inputs=[msg_input, chatbot, current_chat, current_user],
        outputs=[chatbot, msg_input, chats_dropdown, current_chat],
    )

    def logout():
        __logger.info("Выходим из программы")
        return (
            None,
            None,
            [],
            gr.update(choices=[]),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    logout_btn.click(
        logout,
        outputs=[
            current_user,
            current_chat,
            chatbot,
            chats_dropdown,
            login_column,
            main_column,
        ],
    )

    def toggle_files_panel(is_visible):
        return gr.update(visible=not is_visible), not is_visible

    files_btn.click(
        toggle_files_panel, inputs=files_visible, outputs=[files_column, files_visible]
    )

    # def upload_handler(files, user_id, chat_id):
    #     if not files or not user_id or not chat_id:
    #         return gr.update()

    #     filenames = save_files(user_id, chat_id, files)
    #     return gr.update(choices=filenames)

    # upload_files.change(
    #     upload_handler,
    #     inputs=[upload_files, current_user, current_chat],
    #     outputs=files_dropdown,
    # )

    async def send_file_to_rag(file_path: str):
        """
        Вспомогательная функция для отправки одного файла в RAG сервис.
        """
        url = "http://rag_service:8000/upload_and_run"
        timeout = httpx.Timeout(60.0, connect=10.0) # Увеличиваем таймаут для больших файлов

        __logger.info(f'Отправляем ФАЙЛ: {file_path}')

        filename = os.path.basename(file_path)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Открываем файл в бинарном режиме
                with open(file_path, "rb") as f:
                    # Формируем multipart/form-data.
                    # Ключ 'file' обязателен, т.к. в FastAPI получателе: file: UploadFile = File(...)
                    files_payload = {"file": (filename, f, "application/octet-stream")}

                    response = await client.post(url, files=files_payload)
                    response.raise_for_status()

                    __logger.info(f"Файл {filename} успешно отправлен в RAG сервис. Ответ: {response.json()}")
                    return True
        except httpx.HTTPStatusError as e:
            __logger.error(f"RAG сервис вернул ошибку для {filename}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            __logger.error(f"Не удалось подключиться к RAG сервису для {filename}: {e}")
        except Exception as e:
            __logger.error(f"Непредвиденная ошибка при отправке {filename}: {e}")

        return False

    async def upload_handler(files, user_id, chat_id):
        if not files or not user_id or not chat_id:
            return gr.update()

        __logger.info(f'Обработчик файлов в upload_files')

        # 1. Сначала сохраняем файлы локально (для отображения в UI и скачивания)
        # save_files оставляем синхронным, если он быстрый, или можно вынести в thread pool,
        # но обычно сохранение на диск достаточно быстрое.
        filenames = save_files(user_id, chat_id, files)

        # 2. Асинхронно отправляем файлы в RAG сервис
        # Создаем задачи для каждого файла
        tasks = []
        for file_obj in files:
            # Gradio передает file_obj, у которого есть атрибут name (путь к временному файлу)
            tasks.append(send_file_to_rag(file_obj.name))

        # Запускаем все отправки параллельно
        if tasks:
            await asyncio.gather(*tasks)

        # 3. Обновляем выпадающий список (используя имена локально сохраненных файлов)
        return gr.update(choices=filenames)


    upload_files.change(
        upload_handler,
        inputs=[upload_files, current_user, current_chat],
        outputs=files_dropdown,
    )

    def download_handler(filename, user_id, chat_id):
        if not filename:
            return None

        return get_file_path(user_id, chat_id, filename)

    files_dropdown.change(
        download_handler,
        inputs=[files_dropdown, current_user, current_chat],
        outputs=download_file,
    )
