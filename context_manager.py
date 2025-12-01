# -*- coding: utf-8 -*-
"""
Модуль для управления контекстом и историей диалогов пользователей
"""
from pathlib import Path
from typing import Dict
from ai_assistant import ChatAssistant
from config import (
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_MESSAGE,
    DEFAULT_TEMPERATURE,
    HISTORY_FILE_TEMPLATE,
    TXT_HISTORY_FILE_TEMPLATE,
    OLD_HISTORY_JSON,
    OLD_HISTORY_TXT
)
from logger import log_error, log_app_event

# Словарь для хранения ассистентов для каждого пользователя
user_assistants: Dict[int, ChatAssistant] = {}

# Флаг для отслеживания, были ли удалены старые файлы
_old_files_cleaned = False


def get_user_assistant(user_id: int) -> ChatAssistant:
    """
    Получает или создает ассистента для пользователя.
    Каждый пользователь имеет свою историю диалога.
    
    Args:
        user_id: ID пользователя Telegram
        
    Returns:
        ChatAssistant: Экземпляр ассистента для пользователя
    """
    if user_id not in user_assistants:
        history_file = HISTORY_FILE_TEMPLATE.format(user_id=user_id)
        user_assistants[user_id] = ChatAssistant(
            model=DEFAULT_MODEL,
            system_message=DEFAULT_SYSTEM_MESSAGE,
            history_file=history_file,
            temperature=DEFAULT_TEMPERATURE
        )
    return user_assistants[user_id]


def save_user_history_to_txt(user_id: int):
    """
    Автоматически сохраняет историю пользователя в txt файл.
    Также удаляет старые файлы истории без user_id при первом сохранении.
    
    Args:
        user_id: ID пользователя Telegram
    """
    global _old_files_cleaned
    
    assistant = get_user_assistant(user_id)
    output_file = TXT_HISTORY_FILE_TEMPLATE.format(user_id=user_id)
    assistant.export_history_to_text(output_file)
    
    # Удаляем старые файлы истории без user_id один раз при первом сохранении
    # Это файлы от старых версий бота, которые больше не используются
    if not _old_files_cleaned:
        old_json_file = Path(OLD_HISTORY_JSON)
        old_txt_file = Path(OLD_HISTORY_TXT)
        
        if old_json_file.exists():
            try:
                old_json_file.unlink()
                print(f"🗑️ Удален старый файл: {old_json_file}")
                log_app_event("Удален старый файл истории", {"file": str(old_json_file)})
            except Exception as e:
                print(f"⚠️ Не удалось удалить {old_json_file}: {e}")
                log_error(e, context={"action": "delete_old_file", "file": str(old_json_file)})
        
        if old_txt_file.exists():
            try:
                old_txt_file.unlink()
                print(f"🗑️ Удален старый файл: {old_txt_file}")
                log_app_event("Удален старый файл истории", {"file": str(old_txt_file)})
            except Exception as e:
                print(f"⚠️ Не удалось удалить {old_txt_file}: {e}")
                log_error(e, context={"action": "delete_old_file", "file": str(old_txt_file)})
        
        _old_files_cleaned = True


def get_history_file_path(user_id: int) -> str:
    """
    Возвращает путь к файлу истории для пользователя.
    
    Args:
        user_id: ID пользователя Telegram
        
    Returns:
        str: Путь к файлу истории
    """
    return TXT_HISTORY_FILE_TEMPLATE.format(user_id=user_id)

