import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(
        self,
        name: str,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 3,
        rotating_in_file: bool = True,
        use_log: bool = True,
    ):
        self.use_log = use_log
        # Создание объекта
        self.logger = logging.getLogger(name)

        # Определение уровня логгирования
        log_level = logging.DEBUG
        self.logger.setLevel(log_level)

        # Запрещаем передачу от дочерних узлов
        self.logger.propagate = False

        # Защита от дублирования хендлеровм
        if self.logger.handlers:
            return

        # Создание папки для логгов
        log_path = Path(".logs")
        log_path.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # Файл логов с ротацией
        if rotating_in_file:
            log_file = log_path / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)


    def debug(self, msg: str):
        if self.use_log:
            self.logger.debug(msg)


    def info(self, msg: str):
        if self.use_log:
            self.logger.info(msg)


    def warning(self, msg: str):
        if self.use_log:
            self.logger.warning(msg)


    def error(self, msg: str):
        if self.use_log:
            self.logger.error(msg)


    def exception(self, msg: str):
        if self.use_log:
            self.logger.exception(msg)
