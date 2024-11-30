from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
import logging
from logging.handlers import RotatingFileHandler
import os


class Settings(BaseSettings):
    bot_token: SecretStr
    db_name: str
    db_user: str
    db_password: SecretStr
    db_host: str
    db_port: int

    date_time_format: str
    date_time_format_print: str

    log_file_path: str
    log_error_file_path: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()


def setup_logging(level=logging.INFO):
    import os

    # Создаем директории для логов, используя os.path.join для кроссплатформенности
    log_dir = os.path.dirname(os.path.abspath(config.log_file_path))
    error_log_dir = os.path.dirname(os.path.abspath(config.log_error_file_path))

    # Создаем директории рекурсивно
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(error_log_dir, exist_ok=True)

    # Создаем форматтер для логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Основной обработчик для всех логов
    main_handler = RotatingFileHandler(
        os.path.abspath(config.log_file_path),
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    main_handler.setFormatter(formatter)

    # Обработчик только для ошибок
    error_handler = RotatingFileHandler(
        os.path.abspath(config.log_error_file_path),
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Настраиваем корневой логгер
    logging.basicConfig(
        level=level, handlers=[console_handler, main_handler, error_handler]
    )