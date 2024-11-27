import logging


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Вывод в консоль
            #     RotatingFileHandler(
            #         "bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
            #     ),  # Ротация логов
        ],
    )

    # Настроим уровень логирования для httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)
