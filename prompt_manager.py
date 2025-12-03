# -*- coding: utf-8 -*-
"""
Модуль для управления промптами и генерации приветственных сообщений
"""
import json
from pathlib import Path
from typing import Optional, Dict
from ai_assistant import ChatAssistant
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from logger import log_error, log_app_event

# Путь к файлу с промптом приветствия
WELCOME_PROMPT_FILE = "welcome_prompt.json"


def load_prompt_config(file_path: str) -> Optional[Dict]:
    """
    Загружает конфигурацию промпта из JSON файла.
    
    Args:
        file_path: Путь к JSON файлу с промптом
        
    Returns:
        Dict с конфигурацией промпта или None в случае ошибки
    """
    try:
        prompt_path = Path(file_path)
        if not prompt_path.exists():
            log_app_event("Файл промпта не найден", {"file": file_path})
            return None
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        log_error(e, context={"action": "load_prompt_config", "file": file_path})
        return None


def generate_welcome_message(user_name: str, model: str = DEFAULT_MODEL, 
                            temperature: float = DEFAULT_TEMPERATURE, language: str = "ru") -> str:
    """
    Генерирует приветственное сообщение с использованием AI на основе промпта.
    
    Args:
        user_name: Имя пользователя
        model: Модель AI для генерации
        temperature: Температура для генерации
        language: Язык для генерации сообщения (ru/en)
        
    Returns:
        str: Сгенерированное приветственное сообщение или сообщение по умолчанию
    """
    try:
        # Загружаем конфигурацию промпта
        prompt_config = load_prompt_config(WELCOME_PROMPT_FILE)
        
        if not prompt_config:
            # Если промпт не загружен, используем стандартное приветствие
            return get_default_welcome_message(user_name, language)
        
        # Формируем промпт для AI с учетом языка
        if language == "en":
            # Английская версия промпта
            role = "You are a welcome module for a Telegram bot responsible for the first interaction with the user. Your task is to create a short, friendly and clear welcome message that prepares the user for further actions."
            context = "The bot is used in a business environment. The user may be visiting for the first time or after a long break. The greeting should be neutral, professional, without excessive emotionality, but not dry. It is important to show that the bot is ready to help and guide to the next step."
            task = "Formulate a welcome message that includes a short greeting, explanation of the bot's capabilities and an invitation to continue working."
            format_requirements = "Output only the welcome text without explanations. Short message of 2-3 sentences."
            language_instruction = "\n\nIMPORTANT: Generate the welcome message in English language only."
            user_prompt = f"User name: {user_name}"
        else:
            # Русская версия промпта
            role = prompt_config.get("role", "")
            context = prompt_config.get("context", "")
            task = prompt_config.get("task", "")
            format_requirements = prompt_config.get("format", "")
            language_instruction = "\n\nВАЖНО: Сгенерируй приветственное сообщение только на русском языке."
            user_prompt = f"Имя пользователя: {user_name}"
        
        full_prompt = f"""{role}

{context}

{task}

{format_requirements}
{language_instruction}

{user_prompt}"""
        
        # Создаем временного ассистента для генерации приветствия
        # Используем отдельный файл истории, чтобы не смешивать с основным диалогом
        if language == "en":
            system_msg = "You are a professional assistant for creating welcome messages."
        else:
            system_msg = "Ты профессиональный помощник для создания приветственных сообщений."
        
        temp_assistant = ChatAssistant(
            model=model,
            system_message=system_msg,
            history_file=None,  # Не сохраняем историю для приветствия
            temperature=temperature
        )
        
        # Генерируем приветствие
        response, _ = temp_assistant.get_response(full_prompt)
        
        # Очищаем ответ от лишних символов и форматируем
        welcome_text = response.strip()
        
        # Добавляем информацию о боте, если сообщение слишком короткое
        if len(welcome_text) < 50:
            if language == "en":
                welcome_text += f"\n\nUse the menu below to manage settings."
            else:
                welcome_text += f"\n\nИспользуйте меню ниже для управления настройками."
        
        log_app_event("Сгенерировано приветственное сообщение", {
            "model": model,
            "user_name": user_name,
            "message_length": len(welcome_text)
        })
        
        return welcome_text
        
    except Exception as e:
        log_error(e, context={
            "action": "generate_welcome_message",
            "user_name": user_name,
            "model": model
        })
        # В случае ошибки возвращаем стандартное приветствие
        return get_default_welcome_message(user_name, language)


def get_default_welcome_message(user_name: str, language: str = "ru") -> str:
    """
    Возвращает стандартное приветственное сообщение.
    
    Args:
        user_name: Имя пользователя
        language: Язык сообщения (ru/en)
        
    Returns:
        str: Стандартное приветственное сообщение
    """
    if language == "en":
        return (
            f"Welcome, {user_name}!\n\n"
            f"I'm an AI assistant ready to help you with various tasks. "
            f"Use the menu below to manage settings and get started."
        )
    else:
        return (
            f"Добро пожаловать, {user_name}!\n\n"
            f"Я AI-ассистент, готовый помочь вам с различными задачами. "
            f"Используйте меню ниже для управления настройками и начала работы."
        )

