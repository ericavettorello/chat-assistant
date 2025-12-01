# -*- coding: utf-8 -*-
"""
Конфигурационный файл с настройками проекта
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# ========== Настройки AI моделей ==========
# Модель по умолчанию
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_SYSTEM_MESSAGE = "Ты дружелюбный и умный помощник. Отвечай подробно и полезно."
DEFAULT_TEMPERATURE = 1.0

# Доступные модели
AVAILABLE_MODELS = {
    "gpt-3.5-turbo": "GPT-3.5 Turbo (быстрая)",
    "gpt-4o": "GPT-4o (продвинутая)",
    "gpt-5-pro": "GPT-5 Pro (self-reasoning)",
    "o1": "O1 (self-reasoning)",
    "o3": "O3 (self-reasoning)",
    "claude-sonnet-4-5-20250929": "Claude 4.5 Sonnet (с reasoning)"
}

# ========== Настройки API ==========
# API ключи из переменных окружения
PROXY_API_KEY = os.getenv("ProxyAPI_KEY")
TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY")

# URL прокси-серверов
OPENAI_BASE_URL = "https://api.proxyapi.ru/openai/v1"
ANTHROPIC_BASE_URL = "https://api.proxyapi.ru/anthropic"

# Флаг для определения, поддерживает ли прокси-сервер reasoning параметры
# Прокси-сервер api.proxyapi.ru не поддерживает reasoning_effort для OpenAI
PROXY_SUPPORTS_REASONING = False

# ========== Настройки истории ==========
# Шаблон имени файла истории для пользователей
HISTORY_FILE_TEMPLATE = "chat_history_{user_id}.json"
TXT_HISTORY_FILE_TEMPLATE = "chat_history_{user_id}.txt"

# Старые файлы истории (без user_id) - для очистки
OLD_HISTORY_JSON = "chat_history.json"
OLD_HISTORY_TXT = "chat_history.txt"

# ========== Настройки Telegram ==========
# Максимальная длина сообщения Telegram
MAX_MESSAGE_LENGTH = 4096

