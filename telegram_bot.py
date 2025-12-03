# -*- coding: utf-8 -*-
import sys
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Импортируем модули проекта
from ai_assistant import ChatAssistant
from config import (
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_MESSAGE,
    DEFAULT_TEMPERATURE,
    AVAILABLE_MODELS,
    TELEGRAM_BOT_KEY,
    MAX_MESSAGE_LENGTH
)
from context_manager import (
    get_user_assistant,
    save_user_history_to_txt,
    get_history_file_path,
    get_user_language,
    set_user_language
)
from logger import log_error, log_app_event
from prompt_manager import generate_welcome_message
from language_manager import get_text, format_text

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def create_temperature_keyboard(current_temp: float, language: str = "ru") -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора температуры"""
    if language == "en":
        temperatures = [
            (0.0, "deterministic"),
            (0.3, "low"),
            (0.7, "medium"),
            (1.0, "standard"),
            (1.3, "high"),
            (1.7, "very high"),
            (2.0, "maximum")
        ]
    else:
        temperatures = [
            (0.0, "детерминированный"),
            (0.3, "низкая"),
            (0.7, "средняя"),
            (1.0, "стандартная"),
            (1.3, "высокая"),
            (1.7, "очень высокая"),
            (2.0, "максимальная")
        ]
    
    keyboard = []
    for temp, label in temperatures:
        # Проверяем, является ли это текущей температурой (с учетом погрешности)
        is_current = abs(temp - current_temp) < 0.01
        button_text = f"{temp} ({label})"
        if is_current:
            button_text += " ✅"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"temp_{temp}")])
    
    keyboard.append([InlineKeyboardButton(get_text("back", language), callback_data="back_to_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def create_language_keyboard(current_language: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора языка"""
    keyboard = []
    
    keyboard.append([InlineKeyboardButton(
        "🇷🇺 Русский" + (" ✅" if current_language == "ru" else ""),
        callback_data="lang_ru"
    )])
    keyboard.append([InlineKeyboardButton(
        "🇬🇧 English" + (" ✅" if current_language == "en" else ""),
        callback_data="lang_en"
    )])
    keyboard.append([InlineKeyboardButton(
        get_text("back", current_language),
        callback_data="back_to_menu"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def create_model_keyboard(current_model: str, language: str = "ru") -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора модели"""
    keyboard = []
    
    # OpenAI модели
    keyboard.append([InlineKeyboardButton(
        "🤖 " + get_text("model_gpt_3_5", language) + (" ✅" if current_model == "gpt-3.5-turbo" else ""),
        callback_data="model_gpt-3.5-turbo"
    )])
    keyboard.append([InlineKeyboardButton(
        "🚀 " + get_text("model_gpt_4o", language) + (" ✅" if current_model == "gpt-4o" else ""),
        callback_data="model_gpt-4o"
    )])
    keyboard.append([InlineKeyboardButton(
        "🧠 " + get_text("model_gpt_5_pro", language) + (" ✅" if current_model == "gpt-5-pro" else ""),
        callback_data="model_gpt-5-pro"
    )])
    keyboard.append([InlineKeyboardButton(
        "🔮 " + get_text("model_o1", language) + (" ✅" if current_model == "o1" else ""),
        callback_data="model_o1"
    )])
    keyboard.append([InlineKeyboardButton(
        "🔮 " + get_text("model_o3", language) + (" ✅" if current_model == "o3" else ""),
        callback_data="model_o3"
    )])
    
    # Claude модели
    keyboard.append([InlineKeyboardButton(
        "💎 " + get_text("model_claude", language) + (" ✅" if current_model == "claude-sonnet-4-5-20250929" else ""),
        callback_data="model_claude-sonnet-4-5-20250929"
    )])
    
    # Дополнительные кнопки
    keyboard.append([
        InlineKeyboardButton("🌡️ " + get_text("temperature_settings", language).replace("🌡️ ", ""), callback_data="set_temperature")
    ])
    keyboard.append([
        InlineKeyboardButton("🌐 " + get_text("language", language).replace("🌐 ", ""), callback_data="set_language")
    ])
    keyboard.append([
        InlineKeyboardButton(get_text("download_history", language), callback_data="download_history"),
        InlineKeyboardButton(get_text("clear_history", language), callback_data="clear_history")
    ])
    keyboard.append([
        InlineKeyboardButton(get_text("exit_info", language), callback_data="show_exit_info"),
        InlineKeyboardButton(get_text("close_menu", language), callback_data="close_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - сразу открывает главное меню"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        user_name = update.effective_user.first_name or "Пользователь"
        assistant = get_user_assistant(user_id)
        language = get_user_language(user_id)
        
        log_app_event("Пользователь запустил бота", {
            "user_id": user_id,
            "username": username,
            "model": assistant.model,
            "language": language
        })
        
        # Генерируем приветственное сообщение через AI
        try:
            welcome_text = generate_welcome_message(
                user_name=user_name,
                model=assistant.model,
                temperature=assistant.temperature,
                language=language
            )
        except Exception as e:
            log_error(e, context={"action": "generate_welcome", "user_id": user_id})
            # Используем стандартное приветствие в случае ошибки
            welcome_text = format_text("welcome_message", language, name=user_name)
        
        # Добавляем техническую информацию
        welcome_message = (
            f"{welcome_text}\n\n"
            f"📊 {get_text('current_model', language)}: {assistant.model}\n"
            f"🌡️ {get_text('current_temperature', language)}: {assistant.temperature}\n\n"
            f"💡 {get_text('use_menu_below', language)}"
        )
        
        keyboard = create_model_keyboard(assistant.model, language)
        await update.message.reply_text(welcome_message, reply_markup=keyboard)
    except Exception as e:
        user_id = update.effective_user.id if update.effective_user else None
        language = get_user_language(user_id) if user_id else "ru"
        error_msg = f"{get_text('error_startup', language)}: {str(e)}"
        await update.message.reply_text(error_msg)
        log_error(e, context={
            "handler": "start",
            "user_id": user_id
        })


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu - открывает главное меню"""
    try:
        user_id = update.effective_user.id
        assistant = get_user_assistant(user_id)
        language = get_user_language(user_id)
        
        menu_text = (
            f"{get_text('main_menu', language)}\n\n"
            f"📊 {get_text('current_model', language)}: {assistant.model}\n"
            f"🌡️ {get_text('current_temperature', language)}: {assistant.temperature}\n"
            f"{get_text('select_model_or_action', language)}"
        )
        
        keyboard = create_model_keyboard(assistant.model, language)
        await update.message.reply_text(menu_text, reply_markup=keyboard)
    except Exception as e:
        user_id = update.effective_user.id if update.effective_user else None
        language = get_user_language(user_id) if user_id else "ru"
        error_msg = f"{get_text('error_menu', language)}: {str(e)}"
        await update.message.reply_text(error_msg)
        log_error(e, context={
            "handler": "menu_command",
            "user_id": user_id
        })


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки в меню"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    assistant = get_user_assistant(user_id)
    language = get_user_language(user_id)
    
    if query.data.startswith("model_"):
        # Смена модели
        new_model = query.data.replace("model_", "")
        old_model = assistant.model
        assistant.model = new_model
        assistant.save_history()
        
        log_app_event("Пользователь изменил модель", {
            "user_id": user_id,
            "old_model": old_model,
            "new_model": new_model
        })
        
        await query.edit_message_text(
            f"{get_text('model_changed', language)}:\n"
            f"{get_text('was', language)}: {old_model}\n"
            f"{get_text('became', language)}: {new_model}\n\n"
            f"{get_text('now_use_model', language)}",
            reply_markup=create_model_keyboard(new_model, language)
        )
    
    elif query.data == "download_history":
        # Скачать историю
        save_user_history_to_txt(user_id)
        output_file = get_history_file_path(user_id)
        
        if Path(output_file).exists():
            with open(output_file, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=output_file,
                    caption=get_text("history_document", language)
                )
            await query.answer(get_text("history_sent", language))
        else:
            await query.answer(get_text("history_empty", language), show_alert=True)
    
    elif query.data == "clear_history":
        # Очистка истории
        assistant.clear_history(keep_system=True)
        save_user_history_to_txt(user_id)  # Обновляем txt файл
        
        await query.edit_message_text(
            get_text("history_cleared", language),
            reply_markup=create_model_keyboard(assistant.model, language)
        )
    
    elif query.data == "show_exit_info":
        # Показать информацию о выходе
        exit_info = (
            f"{get_text('exit_info_title', language)}\n\n"
            f"{get_text('exit_info_text', language)}"
        )
        await query.message.reply_text(exit_info)
        # Показываем меню снова
        await query.message.reply_text(
            f"{get_text('main_menu', language)}\n\n{get_text('select_model_or_action', language)}",
            reply_markup=create_model_keyboard(assistant.model, language)
        )
    
    elif query.data == "set_temperature":
        # Настройка температуры
        temp_info = (
            f"{get_text('temperature_settings', language)}\n\n"
            f"{get_text('current_temperature_label', language)}: {assistant.temperature}\n\n"
            f"{get_text('temperature_info', language)}\n\n"
            f"{get_text('temperature_note', language)}"
        )
        
        await query.edit_message_text(
            temp_info,
            reply_markup=create_temperature_keyboard(assistant.temperature, language)
        )
    
    elif query.data == "set_language":
        # Настройка языка
        lang_info = (
            f"{get_text('language_settings', language)}\n\n"
            f"{get_text('current_language', language)}: {get_text(f'language_{language}', language)}"
        )
        
        await query.edit_message_text(
            lang_info,
            reply_markup=create_language_keyboard(language)
        )
    
    elif query.data.startswith("lang_"):
        # Установка языка
        new_lang = query.data.replace("lang_", "")
        old_lang = language
        set_user_language(user_id, new_lang)
        language = new_lang  # Обновляем локальную переменную
        
        log_app_event("Пользователь изменил язык", {
            "user_id": user_id,
            "old_language": old_lang,
            "new_language": new_lang
        })
        
        # Сохраняем язык в истории
        assistant.save_history(language=new_lang)
        
        # Генерируем новое приветственное сообщение на новом языке
        user_name = query.from_user.first_name or "User"
        try:
            welcome_text = generate_welcome_message(
                user_name=user_name,
                model=assistant.model,
                temperature=assistant.temperature,
                language=new_lang
            )
        except Exception as e:
            log_error(e, context={"action": "generate_welcome_on_lang_change", "user_id": user_id})
            welcome_text = format_text("welcome_message", new_lang, name=user_name)
        
        # Формируем сообщение с приветствием и информацией о смене языка
        welcome_message = (
            f"{welcome_text}\n\n"
            f"📊 {get_text('current_model', language)}: {assistant.model}\n"
            f"🌡️ {get_text('current_temperature', language)}: {assistant.temperature}\n\n"
            f"✅ {get_text('language_changed', language)}:\n"
            f"{get_text('was', language)}: {get_text(f'language_{old_lang}', language)}\n"
            f"{get_text('became', language)}: {get_text(f'language_{new_lang}', language)}\n\n"
            f"💡 {get_text('use_menu_below', language)}"
        )
        
        await query.edit_message_text(
            welcome_message,
            reply_markup=create_model_keyboard(assistant.model, language)
        )
    
    elif query.data.startswith("temp_"):
        # Установка температуры
        try:
            new_temp = float(query.data.replace("temp_", ""))
            old_temp = assistant.temperature
            assistant.temperature = new_temp
            assistant.save_history()
            
            log_app_event("Пользователь изменил температуру", {
                "user_id": user_id,
                "old_temperature": old_temp,
                "new_temperature": new_temp,
                "model": assistant.model
            })
            
            await query.edit_message_text(
                f"{get_text('temperature_changed', language)}:\n"
                f"{get_text('was', language)}: {old_temp}\n"
                f"{get_text('became', language)}: {new_temp}\n\n"
                f"{get_text('changes_apply_next', language)}",
                reply_markup=create_model_keyboard(assistant.model, language)
            )
        except ValueError as e:
            log_error(e, context={
                "handler": "temperature_set",
                "user_id": user_id,
                "temperature_value": query.data
            })
            await query.answer(f"{get_text('error', language)}: {get_text('temperature_changed', language).lower()}", show_alert=True)
    
    elif query.data == "back_to_menu":
        # Возврат в главное меню
        menu_text = (
            f"{get_text('main_menu', language)}\n\n"
            f"📊 {get_text('current_model', language)}: {assistant.model}\n"
            f"🌡️ {get_text('current_temperature', language)}: {assistant.temperature}\n"
            f"{get_text('select_model_or_action', language)}"
        )
        await query.edit_message_text(
            menu_text,
            reply_markup=create_model_keyboard(assistant.model, language)
        )
    
    elif query.data == "close_menu":
        # Закрыть меню
        await query.edit_message_text(
            f"{get_text('menu_closed', language)}\n\n"
            f"{get_text('menu_help', language)}"
        )


async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /exit - объясняет как выйти из бота"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    exit_text = (
        f"{get_text('exit_info_title', language)}\n\n"
        f"{get_text('exit_info_text', language)}"
    )
    await update.message.reply_text(exit_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    help_text = (
        f"{get_text('help_title', language)}:\n\n"
        f"{get_text('help_commands', language)}\n\n"
        f"{get_text('help_tip', language)}\n\n"
        f"{get_text('help_history', language)}\n"
        f"{get_text('help_export', language)}\n\n"
        f"{get_text('help_exit', language)}"
    )
    await update.message.reply_text(help_text)


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /model для выбора модели"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)
    language = get_user_language(user_id)
    
    if context.args:
        new_model = " ".join(context.args)
        old_model = assistant.model
        assistant.model = new_model
        
        # Сохраняем новую модель в историю
        assistant.save_history()
        
        await update.message.reply_text(
            f"{get_text('model_changed', language)}:\n"
            f"{get_text('was', language)}: {old_model}\n"
            f"{get_text('became', language)}: {new_model}"
        )
    else:
        models_list = (
            f"{get_text('models_available', language)}\n\n"
            f"{get_text('models_openai', language)}\n"
            f"  • gpt-3.5-turbo {get_text('model_fast_standard', language)}\n"
            f"  • gpt-4o {get_text('model_advanced', language)}\n"
            f"  • gpt-5-pro {get_text('model_self_reasoning', language)}\n"
            f"  • o1, o3 {get_text('model_self_reasoning_models', language)}\n\n"
            f"{get_text('models_anthropic', language)}\n"
            f"  • claude-sonnet-4-5-20250929 ({get_text('model_claude', language)})\n\n"
            f"📊 {get_text('current_model', language)}: {assistant.model}\n\n"
            f"{get_text('models_usage', language)}"
        )
        await update.message.reply_text(models_list)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clear для очистки истории"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)
    
    assistant.clear_history(keep_system=True)
    
    await update.message.reply_text(
        "🗑️ История диалога очищена!\n"
        "Системное сообщение сохранено."
    )


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /export для экспорта истории"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    # Обновляем txt файл перед отправкой
    save_user_history_to_txt(user_id)
    output_file = get_history_file_path(user_id)
    
    # Отправляем файл пользователю
    if Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        with open(output_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=output_file,
                caption=get_text("export_caption", language)
            )
    else:
        await update.message.reply_text(get_text("export_error", language))


async def temperature_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /temperature для настройки температуры"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)
    language = get_user_language(user_id)
    
    if context.args:
        try:
            new_temp = float(context.args[0])
            if not (0.0 <= new_temp <= 2.0):
                await update.message.reply_text(
                    get_text("temperature_range_error", language)
                )
                return
            
            old_temp = assistant.temperature
            assistant.temperature = new_temp
            assistant.save_history()
            
            await update.message.reply_text(
                f"{get_text('temperature_changed', language)}:\n"
                f"{get_text('was', language)}: {old_temp}\n"
                f"{get_text('became', language)}: {new_temp}\n\n"
                f"{get_text('changes_apply_next', language)}\n"
                f"{get_text('temperature_note', language)}"
            )
        except ValueError:
            await update.message.reply_text(
                f"{get_text('temperature_format_error', language)}\n"
                f"{get_text('temperature_usage', language)}\n"
                f"{get_text('temperature_example', language)}"
            )
    else:
        temp_info = (
            f"{get_text('temperature_settings', language)}\n\n"
            f"{get_text('current_temperature_label', language)}: {assistant.temperature}\n\n"
            f"{get_text('temperature_info', language)}\n\n"
            f"{get_text('temperature_usage', language)}\n"
            f"{get_text('temperature_example', language)}\n\n"
            f"{get_text('temperature_note', language)}"
        )
        await update.message.reply_text(temp_info)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text.strip().lower()
    language = get_user_language(user_id)
    
    # Если пользователь написал "exit" или "меню", открываем главное меню
    if user_message in ['exit', 'меню', 'menu']:
        await menu_command(update, context)
        return
    
    # Показываем, что бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        assistant = get_user_assistant(user_id)
        
        # Логируем запрос пользователя
        log_app_event("Получен запрос от пользователя", {
            "user_id": user_id,
            "model": assistant.model,
            "message_length": len(update.message.text),
            "language": language
        })
        
        # Получаем ответ от ассистента (используем оригинальный текст, не lower)
        response, metrics = assistant.get_response(update.message.text)
        
        # Автоматически сохраняем историю в txt после каждого сообщения
        save_user_history_to_txt(user_id)
        
        # Формируем ответ с метриками, если доступны
        reply_text = response
        
        if metrics:
            metrics_text = f"\n\n{get_text('metrics_title', language)}\n"
            if assistant.is_claude_model():
                metrics_text += f"{get_text('metrics_input_tokens', language)} {metrics.get('input_tokens', 'N/A')}\n"
                metrics_text += f"{get_text('metrics_output_tokens', language)} {metrics.get('output_tokens', 'N/A')}"
                if metrics.get('cache_creation_input_tokens'):
                    metrics_text += f"\n{get_text('metrics_cache_creation', language)} {metrics.get('cache_creation_input_tokens')}"
                if metrics.get('cache_read_input_tokens'):
                    metrics_text += f"\n{get_text('metrics_cache_read', language)} {metrics.get('cache_read_input_tokens')}"
            else:
                metrics_text += f"{get_text('metrics_prompt_tokens', language)} {metrics.get('prompt_tokens', 'N/A')}\n"
                metrics_text += f"{get_text('metrics_completion_tokens', language)} {metrics.get('completion_tokens', 'N/A')}\n"
                metrics_text += f"{get_text('metrics_total_tokens', language)} {metrics.get('total_tokens', 'N/A')}"
            reply_text += metrics_text
        
        # Создаем клавиатуру с кнопкой меню
        menu_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 " + get_text("menu", language), callback_data="back_to_menu")]
        ])
        
        # Отправляем ответ (разбиваем на части, если слишком длинный)
        if len(reply_text) > MAX_MESSAGE_LENGTH:
            # Telegram ограничивает длину сообщения
            parts = [reply_text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(reply_text), MAX_MESSAGE_LENGTH)]
            # Кнопку меню добавляем только к последнему сообщению
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    await update.message.reply_text(part, reply_markup=menu_keyboard)
                else:
                    await update.message.reply_text(part)
        else:
            await update.message.reply_text(reply_text, reply_markup=menu_keyboard)
            
    except Exception as e:
        language = get_user_language(user_id) if 'user_id' in locals() else "ru"
        error_message = f"{get_text('error_processing', language)}: {str(e)}"
        await update.message.reply_text(error_message)
        log_error(e, context={
            "handler": "handle_message",
            "user_id": user_id,
            "model": assistant.model if 'assistant' in locals() else None
        })


def main():
    """Основная функция для запуска бота"""
    # Получаем токен бота из конфигурации
    bot_token = TELEGRAM_BOT_KEY
    
    if not bot_token:
        error_msg = "❌ Ошибка: TELEGRAM_BOT_KEY не найден в .env файле!"
        print(error_msg)
        log_app_event("Ошибка запуска бота", {"reason": "TELEGRAM_BOT_KEY не найден"})
        return
    
    try:
        # Регистрируем команды в боковой панели бота
        commands = [
            BotCommand("start", "Начать работу с ботом (открывает меню)"),
            BotCommand("menu", "Открыть главное меню"),
            BotCommand("model", "Выбрать модель AI"),
            BotCommand("temperature", "Настроить температуру (0.0-2.0)"),
            BotCommand("clear", "Очистить историю диалога"),
            BotCommand("export", "Скачать историю диалога"),
            BotCommand("exit", "Информация о выходе из бота"),
            BotCommand("help", "Показать справку по командам")
        ]
        
        # Создаем приложение с инициализацией команд
        async def post_init(app: Application) -> None:
            await app.bot.set_my_commands(commands)
            print("✅ Команды зарегистрированы в боковой панели Telegram")
        
        application = Application.builder().token(bot_token).post_init(post_init).build()
        
        # Регистрируем обработчики команд (важен порядок!)
        # Сначала команды, потом текстовые сообщения
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("model", model_command))
        application.add_handler(CommandHandler("temperature", temperature_command))
        application.add_handler(CommandHandler("clear", clear_command))
        application.add_handler(CommandHandler("export", export_command))
        application.add_handler(CommandHandler("exit", exit_command))
        
        # Регистрируем обработчик нажатий на кнопки
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Регистрируем обработчик текстовых сообщений (последним, чтобы не перехватывать команды)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        print("🤖 Telegram бот запущен!")
        print("📋 Команды зарегистрированы в боковой панели")
        print("Нажмите Ctrl+C для остановки")
        log_app_event("Telegram бот запущен", {"status": "running"})
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Игнорируем старые обновления при запуске
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен пользователем")
        log_app_event("Telegram бот остановлен", {"reason": "KeyboardInterrupt"})
    except Exception as e:
        error_msg = f"\n❌ Ошибка при работе бота: {str(e)}"
        print(error_msg)
        print("Убедитесь, что только один экземпляр бота запущен!")
        log_error(e, context={"handler": "main", "action": "bot_startup"})


if __name__ == "__main__":
    main()

