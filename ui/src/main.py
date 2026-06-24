from utils import Logger
from config import settings_ui
from modules.interface import demo
from modules.database import init_db


logger = Logger("main.log")


logger.info("===== Подготовка БД для UI =====")
init_db()


logger.info("===== Начинается процесс запуска UI =====")
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    theme=settings_ui.get_theme_class(),
    share=settings_ui.make_share,
)
logger.info("===== Приложение закрыто =====")
