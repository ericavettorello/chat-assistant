# -*- coding: utf-8 -*-
"""
Модуль для управления языками интерфейса
"""
from typing import Dict
from enum import Enum

class Language(Enum):
    """Поддерживаемые языки"""
    RUSSIAN = "ru"
    ENGLISH = "en"


# Словари с переводами
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        # Общие
        "welcome": "Добро пожаловать",
        "menu": "Меню",
        "close": "Закрыть",
        "back": "Назад",
        "error": "Ошибка",
        "success": "Успешно",
        
        # Приветствие
        "welcome_message": "Добро пожаловать, {name}!\n\nЯ AI-ассистент, готовый помочь вам с различными задачами.",
        "use_menu_below": "Используйте меню ниже для управления настройками.",
        "current_model": "Текущая модель",
        "current_temperature": "Текущая температура",
        
        # Меню
        "main_menu": "📋 Главное меню",
        "select_model_or_action": "Выберите модель или действие:",
        "download_history": "📥 Скачать историю",
        "clear_history": "🗑️ Очистить",
        "exit_info": "🚪 Инфо о выходе",
        "close_menu": "❌ Закрыть меню",
        "language": "🌐 Язык",
        
        # Модели
        "model_changed": "✅ Модель изменена:",
        "was": "Было",
        "became": "Стало",
        "now_use_model": "💬 Теперь используй эту модель для диалога!",
        "model_gpt_3_5": "GPT-3.5 Turbo",
        "model_gpt_4o": "GPT-4o",
        "model_gpt_5_pro": "GPT-5 Pro",
        "model_o1": "O1",
        "model_o3": "O3",
        "model_claude": "Claude 4.5 Sonnet",
        
        # Температура
        "temperature_settings": "🌡️ Настройка температуры",
        "current_temperature_label": "Текущая температура",
        "temperature_info": (
            "Температура контролирует случайность ответов:\n"
            "• 0.0-0.3: Детерминированные, точные ответы\n"
            "• 0.7-1.0: Сбалансированные ответы (рекомендуется)\n"
            "• 1.3-2.0: Креативные, разнообразные ответы"
        ),
        "temperature_note": "⚠️ Примечание: Температура работает только для OpenAI моделей.\nДля Claude моделей этот параметр не применяется.",
        "temperature_changed": "✅ Температура изменена:",
        "changes_apply_next": "💡 Изменения применятся к следующим запросам.",
        
        # История
        "history_cleared": "🗑️ История диалога очищена!\nСистемное сообщение сохранено.",
        "history_sent": "✅ История отправлена!",
        "history_empty": "❌ История пуста",
        "history_document": "📄 История диалога",
        
        # Выход
        "exit_info_title": "🚪 Выход из бота",
        "exit_info_text": (
            "Для выхода из бота у вас есть несколько вариантов:\n\n"
            "1️⃣ Просто закройте чат с ботом в Telegram\n"
            "2️⃣ Остановите бота на сервере (если у вас есть доступ)\n"
            "3️⃣ Просто перестаньте отправлять сообщения\n\n"
            "💡 Бот продолжит работать в фоновом режиме.\n"
            "Ваша история диалога сохранится и будет доступна при следующем запуске.\n\n"
            "📥 Не забудьте скачать историю перед выходом, если нужно!\n"
            "Используйте /export или кнопку в меню."
        ),
        "menu_closed": "✅ Меню закрыто.",
        "menu_help": (
            "💡 Для открытия меню:\n"
            "• Напишите: exit, меню или menu\n"
            "• Используйте команду: /menu\n"
            "• Или нажмите /start"
        ),
        
        # Язык
        "language_settings": "🌐 Настройка языка",
        "current_language": "Текущий язык",
        "language_changed": "✅ Язык изменен:",
        "language_ru": "Русский",
        "language_en": "English",
        
        # Команды
        "typing": "Печатает...",
        "error_processing": "❌ Ошибка при обработке запроса:",
        "error_startup": "❌ Ошибка при запуске:",
        "error_menu": "❌ Ошибка при открытии меню:",
    },
    "en": {
        # General
        "welcome": "Welcome",
        "menu": "Menu",
        "close": "Close",
        "back": "Back",
        "error": "Error",
        "success": "Success",
        
        # Welcome
        "welcome_message": "Welcome, {name}!\n\nI'm an AI assistant ready to help you with various tasks.",
        "use_menu_below": "Use the menu below to manage settings.",
        "current_model": "Current model",
        "current_temperature": "Current temperature",
        
        # Menu
        "main_menu": "📋 Main Menu",
        "select_model_or_action": "Select model or action:",
        "download_history": "📥 Download History",
        "clear_history": "🗑️ Clear",
        "exit_info": "🚪 Exit Info",
        "close_menu": "❌ Close Menu",
        "language": "🌐 Language",
        
        # Models
        "model_changed": "✅ Model changed:",
        "was": "Was",
        "became": "Became",
        "now_use_model": "💬 Now use this model for dialogue!",
        
        # Temperature
        "temperature_settings": "🌡️ Temperature Settings",
        "current_temperature_label": "Current temperature",
        "temperature_info": (
            "Temperature controls response randomness:\n"
            "• 0.0-0.3: Deterministic, precise responses\n"
            "• 0.7-1.0: Balanced responses (recommended)\n"
            "• 1.3-2.0: Creative, diverse responses"
        ),
        "temperature_note": "⚠️ Note: Temperature works only for OpenAI models.\nFor Claude models this parameter is not applied.",
        "temperature_changed": "✅ Temperature changed:",
        "changes_apply_next": "💡 Changes will apply to next requests.",
        
        # History
        "history_cleared": "🗑️ Chat history cleared!\nSystem message preserved.",
        "history_sent": "✅ History sent!",
        "history_empty": "❌ History is empty",
        "history_document": "📄 Chat History",
        
        # Exit
        "exit_info_title": "🚪 Exit from Bot",
        "exit_info_text": (
            "To exit the bot, you have several options:\n\n"
            "1️⃣ Simply close the chat with the bot in Telegram\n"
            "2️⃣ Stop the bot on the server (if you have access)\n"
            "3️⃣ Just stop sending messages\n\n"
            "💡 The bot will continue running in the background.\n"
            "Your chat history will be saved and available on next launch.\n\n"
            "📥 Don't forget to download history before exiting if needed!\n"
            "Use /export or the button in the menu."
        ),
        "menu_closed": "✅ Menu closed.",
        "menu_help": (
            "💡 To open menu:\n"
            "• Type: exit, меню or menu\n"
            "• Use command: /menu\n"
            "• Or press /start"
        ),
        
        # Language
        "language_settings": "🌐 Language Settings",
        "current_language": "Current language",
        "language_changed": "✅ Language changed:",
        "language_ru": "Русский",
        "language_en": "English",
        
        # Commands
        "typing": "Typing...",
        "error_processing": "❌ Error processing request:",
        "error_startup": "❌ Error on startup:",
        "error_menu": "❌ Error opening menu:",
        
        # Bot Commands descriptions
        "cmd_start": "Start working with the bot (opens menu)",
        "cmd_menu": "Open main menu",
        "cmd_model": "Select AI model",
        "cmd_temperature": "Set temperature (0.0-2.0)",
        "cmd_clear": "Clear chat history",
        "cmd_export": "Download chat history",
        "cmd_exit": "Exit information",
        "cmd_help": "Show command help",
        
        # Help
        "help_title": "📚 Command Help:",
        "help_commands": (
            "/start - start working with the bot (opens menu)\n"
            "/menu - open main menu (select model, download history)\n"
            "/model - select model\n"
            "/temperature - set temperature (0.0-2.0)\n"
            "/clear - clear chat history\n"
            "/export - download chat history as txt file\n"
            "/exit - exit information\n"
            "/help - show this help"
        ),
        "help_tip": "💡 Just send a message and I'll reply using the selected model!",
        "help_history": "💾 History is automatically saved to txt file.",
        "help_export": "Use /export or the button in the menu to download.",
        "help_exit": "🚪 Use /exit for exit information.",
        
        # Temperature command
        "temperature_range_error": "❌ Error: Temperature must be between 0.0 and 2.0",
        "temperature_format_error": "❌ Error: Invalid temperature format.",
        "temperature_usage": "Usage: /temperature <number from 0.0 to 2.0>",
        "temperature_example": "Example: /temperature 1.0",
        
        # Model descriptions
        "model_gpt_3_5": "GPT-3.5 Turbo",
        "model_gpt_4o": "GPT-4o",
        "model_gpt_5_pro": "GPT-5 Pro",
        "model_o1": "O1",
        "model_o3": "O3",
        "model_claude": "Claude 4.5 Sonnet",
        "models_available": "🤖 Available models:",
        "models_openai": "OpenAI:",
        "models_anthropic": "Anthropic (Claude):",
        "models_usage": "Usage: /model <model_name>",
        "model_fast_standard": "(fast, standard)",
        "model_advanced": "(advanced)",
        "model_self_reasoning": "(self-reasoning)",
        "model_self_reasoning_models": "(self-reasoning models)",
        
        # Metrics
        "metrics_title": "📊 Metrics:",
        "metrics_input_tokens": "• Input tokens:",
        "metrics_output_tokens": "• Output tokens:",
        "metrics_cache_creation": "• Cache creation tokens:",
        "metrics_cache_read": "• Cache read tokens:",
        "metrics_prompt_tokens": "• Prompt tokens:",
        "metrics_completion_tokens": "• Completion tokens:",
        "metrics_total_tokens": "• Total tokens:",
        
        # Export
        "export_caption": "📄 Chat History\n💾 History is automatically saved after each message.",
        "export_error": "❌ History is empty or an error occurred during export",
    }
}


def get_text(key: str, language: str = "ru") -> str:
    """
    Получает переведенный текст по ключу.
    
    Args:
        key: Ключ текста
        language: Код языка (ru/en)
        
    Returns:
        str: Переведенный текст или ключ, если перевод не найден
    """
    lang_code = language if language in TRANSLATIONS else "ru"
    return TRANSLATIONS.get(lang_code, {}).get(key, key)


def format_text(key: str, language: str = "ru", **kwargs) -> str:
    """
    Получает переведенный текст и форматирует его с параметрами.
    
    Args:
        key: Ключ текста
        language: Код языка (ru/en)
        **kwargs: Параметры для форматирования
        
    Returns:
        str: Отформатированный переведенный текст
    """
    text = get_text(key, language)
    try:
        return text.format(**kwargs)
    except KeyError:
        return text

