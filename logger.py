# -*- coding: utf-8 -*-
"""
Модуль для настройки логирования ошибок и параметров запросов
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Создаем директорию для логов, если её нет
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Пути к файлам логов
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
REQUESTS_LOG_FILE = LOGS_DIR / "requests.log"
APP_LOG_FILE = LOGS_DIR / "app.log"

# Формат логов
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Максимальный размер файла лога (10 МБ)
MAX_LOG_SIZE = 10 * 1024 * 1024
# Количество резервных файлов
BACKUP_COUNT = 5


def setup_logger(name: str, log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """
    Настраивает логгер с записью в файл и консоль.
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу лога
        level: Уровень логирования
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Удаляем существующие обработчики, чтобы избежать дублирования
    logger.handlers.clear()
    
    # Форматтер для логов
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Обработчик для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Предотвращаем распространение логов на родительские логгеры
    logger.propagate = False
    
    return logger


# Создаем логгеры для разных целей
error_logger = setup_logger("error_logger", ERROR_LOG_FILE, logging.ERROR)
request_logger = setup_logger("request_logger", REQUESTS_LOG_FILE, logging.INFO)
app_logger = setup_logger("app_logger", APP_LOG_FILE, logging.INFO)


def log_error(error: Exception, context: dict = None):
    """
    Логирует ошибку с контекстом.
    
    Args:
        error: Объект исключения
        context: Дополнительный контекст (словарь)
    """
    error_msg = f"Ошибка: {type(error).__name__}: {str(error)}"
    
    if context:
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg += f" | Контекст: {context_str}"
    
    error_logger.error(error_msg, exc_info=True)


def log_request(service: str, model: str, params: dict, response_time: float = None, 
                tokens: dict = None, user_id: int = None):
    """
    Логирует параметры запроса к API.
    
    Args:
        service: Название сервиса ('OpenAI' или 'Anthropic')
        model: Модель AI
        params: Параметры запроса (без чувствительных данных)
        response_time: Время ответа в секундах
        tokens: Информация о токенах
        user_id: ID пользователя (если есть)
    """
    log_data = {
        "service": service,
        "model": model,
        "user_id": user_id,
        "response_time_sec": response_time,
        "tokens": tokens
    }
    
    # Безопасное логирование параметров (скрываем чувствительные данные)
    safe_params = {}
    for key, value in params.items():
        if key in ['api_key', 'password', 'token']:
            safe_params[key] = "***HIDDEN***"
        elif key == 'messages':
            # Логируем только количество сообщений и длину последнего
            safe_params['messages_count'] = len(value) if isinstance(value, list) else 0
            if value and isinstance(value, list) and len(value) > 0:
                last_msg = value[-1]
                if isinstance(last_msg, dict) and 'content' in last_msg:
                    content = last_msg['content']
                    safe_params['last_message_length'] = len(str(content))
        else:
            safe_params[key] = value
    
    log_data["params"] = safe_params
    
    # Формируем сообщение лога
    log_message = f"[{service}] Модель: {model}"
    if user_id:
        log_message += f" | User ID: {user_id}"
    if response_time:
        log_message += f" | Время ответа: {response_time:.2f}с"
    if tokens:
        if 'total_tokens' in tokens:
            log_message += f" | Токены: {tokens['total_tokens']}"
        elif 'input_tokens' in tokens and 'output_tokens' in tokens:
            log_message += f" | Токены: {tokens['input_tokens']}+{tokens['output_tokens']}"
    
    request_logger.info(log_message)
    request_logger.debug(f"Параметры запроса: {log_data}")


def log_app_event(event: str, details: dict = None):
    """
    Логирует событие приложения.
    
    Args:
        event: Описание события
        details: Дополнительные детали
    """
    message = event
    if details:
        details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
        message += f" | {details_str}"
    
    app_logger.info(message)

