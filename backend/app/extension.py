import logging
from logging.handlers import RotatingFileHandler

from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
cors = CORS(
    supports_credentials=True,
    origins=["http://localhost:5173", "https://duckdns.org", "http://127.0.0.1:5173"],
)
ma = Marshmallow()


def setup_logger(app):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Обработчик для файла (ротация)
    file_handler = RotatingFileHandler(
        "app.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Минимальный уровень для всех обработчиков
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    logger = logging.getLogger(__name__)
    return logger
