# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from test_chat import ChatAssistant

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Загружаем переменные окружения
load_dotenv()

# Словарь для хранения ассистентов для каждого пользователя
user_assistants: dict[int, ChatAssistant] = {}

# Модель по умолчанию
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_SYSTEM_MESSAGE = "Ты дружелюбный и умный помощник. Отвечай подробно и полезно."

# Доступные модели
AVAILABLE_MODELS = {
    "gpt-3.5-turbo": "GPT-3.5 Turbo (быстрая)",
    "gpt-4o": "GPT-4o (продвинутая)",
    "gpt-5-pro": "GPT-5 Pro (self-reasoning)",
    "o1": "O1 (self-reasoning)",
    "o3": "O3 (self-reasoning)",
    "claude-sonnet-4-5-20250929": "Claude 4.5 Sonnet (с reasoning)"
}


def get_user_assistant(user_id: int) -> ChatAssistant:
    """
    Получает или создает ассистента для пользователя.
    Каждый пользователь имеет свою историю диалога.
    """
    if user_id not in user_assistants:
        history_file = f"chat_history_{user_id}.json"
        user_assistants[user_id] = ChatAssistant(
            model=DEFAULT_MODEL,
            system_message=DEFAULT_SYSTEM_MESSAGE,
            history_file=history_file
        )
    return user_assistants[user_id]


def save_user_history_to_txt(user_id: int):
    """Автоматически сохраняет историю пользователя в txt файл"""
    assistant = get_user_assistant(user_id)
    output_file = f"chat_history_{user_id}.txt"
    assistant.export_history_to_text(output_file)


def create_model_keyboard(current_model: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора модели"""
    keyboard = []
    
    # OpenAI модели
    keyboard.append([InlineKeyboardButton(
        "🤖 GPT-3.5 Turbo" + (" ✅" if current_model == "gpt-3.5-turbo" else ""),
        callback_data="model_gpt-3.5-turbo"
    )])
    keyboard.append([InlineKeyboardButton(
        "🚀 GPT-4o" + (" ✅" if current_model == "gpt-4o" else ""),
        callback_data="model_gpt-4o"
    )])
    keyboard.append([InlineKeyboardButton(
        "🧠 GPT-5 Pro" + (" ✅" if current_model == "gpt-5-pro" else ""),
        callback_data="model_gpt-5-pro"
    )])
    keyboard.append([InlineKeyboardButton(
        "🔮 O1" + (" ✅" if current_model == "o1" else ""),
        callback_data="model_o1"
    )])
    keyboard.append([InlineKeyboardButton(
        "🔮 O3" + (" ✅" if current_model == "o3" else ""),
        callback_data="model_o3"
    )])
    
    # Claude модели
    keyboard.append([InlineKeyboardButton(
        "💎 Claude 4.5 Sonnet" + (" ✅" if current_model == "claude-sonnet-4-5-20250929" else ""),
        callback_data="model_claude-sonnet-4-5-20250929"
    )])
    
    # Дополнительные кнопки
    keyboard.append([
        InlineKeyboardButton("📥 Скачать историю", callback_data="download_history"),
        InlineKeyboardButton("🗑️ Очистить", callback_data="clear_history")
    ])
    keyboard.append([
        InlineKeyboardButton("🚪 Инфо о выходе", callback_data="show_exit_info"),
        InlineKeyboardButton("❌ Закрыть меню", callback_data="close_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - сразу открывает главное меню"""
    try:
        user_id = update.effective_user.id
        assistant = get_user_assistant(user_id)
        
        welcome_message = (
            f"👋 Привет, {update.effective_user.first_name}!\n\n"
            f"Я AI-ассистент с поддержкой OpenAI и Claude моделей.\n\n"
            f"📊 Текущая модель: {assistant.model}\n"
            f"💬 Просто отправь мне сообщение, и я отвечу!\n\n"
            f"💾 История диалога автоматически сохраняется в txt файл.\n\n"
            f"📋 Управление:\n"
            f"• Меню ниже (кнопки)\n"
            f"• Напишите 'exit' или 'меню' для открытия меню\n"
            f"• Команды: /menu, /exit, /help\n"
            f"• Боковая панель Telegram (иконка ☰)"
        )
        
        keyboard = create_model_keyboard(assistant.model)
        await update.message.reply_text(welcome_message, reply_markup=keyboard)
    except Exception as e:
        error_msg = f"❌ Ошибка при запуске: {str(e)}"
        await update.message.reply_text(error_msg)
        print(f"Ошибка в start: {e}")  # Для отладки


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu - открывает главное меню"""
    try:
        user_id = update.effective_user.id
        assistant = get_user_assistant(user_id)
        
        menu_text = (
            f"📋 Главное меню\n\n"
            f"📊 Текущая модель: {assistant.model}\n"
            f"Выберите модель или действие:"
        )
        
        keyboard = create_model_keyboard(assistant.model)
        await update.message.reply_text(menu_text, reply_markup=keyboard)
    except Exception as e:
        error_msg = f"❌ Ошибка при открытии меню: {str(e)}"
        await update.message.reply_text(error_msg)
        print(f"Ошибка в menu_command: {e}")  # Для отладки


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки в меню"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    assistant = get_user_assistant(user_id)
    
    if query.data.startswith("model_"):
        # Смена модели
        new_model = query.data.replace("model_", "")
        old_model = assistant.model
        assistant.model = new_model
        assistant.save_history()
        
        await query.edit_message_text(
            f"✅ Модель изменена:\n"
            f"Было: {old_model}\n"
            f"Стало: {new_model}\n\n"
            f"💬 Теперь используй эту модель для диалога!",
            reply_markup=create_model_keyboard(new_model)
        )
    
    elif query.data == "download_history":
        # Скачать историю
        save_user_history_to_txt(user_id)
        output_file = f"chat_history_{user_id}.txt"
        
        if Path(output_file).exists():
            with open(output_file, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=output_file,
                    caption="📄 История диалога"
                )
            await query.answer("✅ История отправлена!")
        else:
            await query.answer("❌ История пуста", show_alert=True)
    
    elif query.data == "clear_history":
        # Очистка истории
        assistant.clear_history(keep_system=True)
        save_user_history_to_txt(user_id)  # Обновляем txt файл
        
        await query.edit_message_text(
            "🗑️ История диалога очищена!\nСистемное сообщение сохранено.",
            reply_markup=create_model_keyboard(assistant.model)
        )
    
    elif query.data == "show_exit_info":
        # Показать информацию о выходе
        exit_info = (
            "🚪 Выход из бота\n\n"
            "Для выхода из бота у вас есть несколько вариантов:\n\n"
            "1️⃣ Просто закройте чат с ботом в Telegram\n"
            "2️⃣ Остановите бота на сервере (если у вас есть доступ)\n"
            "3️⃣ Просто перестаньте отправлять сообщения\n\n"
            "💡 Бот продолжит работать в фоновом режиме.\n"
            "Ваша история диалога сохранится и будет доступна при следующем запуске.\n\n"
            "📥 Не забудьте скачать историю перед выходом, если нужно!\n"
            "Используйте /export или кнопку в меню."
        )
        await query.message.reply_text(exit_info)
        # Показываем меню снова
        await query.message.reply_text(
            "📋 Главное меню\n\nВыберите модель или действие:",
            reply_markup=create_model_keyboard(assistant.model)
        )
    
    elif query.data == "close_menu":
        # Закрыть меню
        await query.edit_message_text(
            "✅ Меню закрыто.\n\n"
            "💡 Для открытия меню:\n"
            "• Напишите: exit, меню или menu\n"
            "• Используйте команду: /menu\n"
            "• Или нажмите /start"
        )


async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /exit - объясняет как выйти из бота"""
    exit_text = (
        "🚪 Выход из бота\n\n"
        "Для выхода из бота у вас есть несколько вариантов:\n\n"
        "1️⃣ Просто закройте чат с ботом в Telegram\n"
        "2️⃣ Остановите бота на сервере (если у вас есть доступ)\n"
        "3️⃣ Просто перестаньте отправлять сообщения\n\n"
        "💡 Бот продолжит работать в фоновом режиме.\n"
        "Ваша история диалога сохранится и будет доступна при следующем запуске.\n\n"
        "📥 Не забудьте скачать историю перед выходом, если нужно!\n"
        "Используйте /export или кнопку в меню."
    )
    await update.message.reply_text(exit_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📚 Справка по командам:\n\n"
        "/start - начать работу с ботом (открывает меню)\n"
        "/menu - открыть главное меню (выбор модели, скачать историю)\n"
        "/model - выбрать модель\n"
        "/clear - очистить историю диалога\n"
        "/export - скачать историю диалога в txt файл\n"
        "/exit - информация о выходе из бота\n"
        "/help - показать эту справку\n\n"
        "💡 Просто отправь сообщение, и я отвечу с использованием выбранной модели!\n\n"
        "💾 История автоматически сохраняется в txt файл.\n"
        "Используй /export или кнопку в меню для скачивания.\n\n"
        "🚪 Используй /exit для информации о выходе из бота."
    )
    await update.message.reply_text(help_text)


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /model для выбора модели"""
    user_id = update.effective_user.id
    assistant = get_user_assistant(user_id)
    
    if context.args:
        new_model = " ".join(context.args)
        old_model = assistant.model
        assistant.model = new_model
        
        # Сохраняем новую модель в историю
        assistant.save_history()
        
        await update.message.reply_text(
            f"✅ Модель изменена:\n"
            f"Было: {old_model}\n"
            f"Стало: {new_model}"
        )
    else:
        models_list = (
            "🤖 Доступные модели:\n\n"
            "OpenAI:\n"
            "  • gpt-3.5-turbo (быстрая, стандартная)\n"
            "  • gpt-4o (продвинутая)\n"
            "  • gpt-5-pro (self-reasoning)\n"
            "  • o1, o3 (self-reasoning модели)\n\n"
            "Anthropic (Claude):\n"
            "  • claude-sonnet-4-5-20250929 (Claude 4.5 Sonnet)\n\n"
            f"📊 Текущая модель: {assistant.model}\n\n"
            "Использование: /model <название_модели>"
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
    
    # Обновляем txt файл перед отправкой
    save_user_history_to_txt(user_id)
    output_file = f"chat_history_{user_id}.txt"
    
    # Отправляем файл пользователю
    if Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        with open(output_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=output_file,
                caption="📄 История диалога\n💾 История автоматически сохраняется после каждого сообщения."
            )
    else:
        await update.message.reply_text("❌ История пуста или произошла ошибка при экспорте")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text.strip().lower()
    
    # Если пользователь написал "exit" или "меню", открываем главное меню
    if user_message in ['exit', 'меню', 'menu']:
        await menu_command(update, context)
        return
    
    # Показываем, что бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        assistant = get_user_assistant(user_id)
        
        # Получаем ответ от ассистента (используем оригинальный текст, не lower)
        response, metrics = assistant.get_response(update.message.text)
        
        # Автоматически сохраняем историю в txt после каждого сообщения
        save_user_history_to_txt(user_id)
        
        # Формируем ответ с метриками, если доступны
        reply_text = response
        
        if metrics:
            metrics_text = "\n\n📊 Метрики:\n"
            if assistant.is_claude_model():
                metrics_text += f"• Входные токены: {metrics.get('input_tokens', 'N/A')}\n"
                metrics_text += f"• Выходные токены: {metrics.get('output_tokens', 'N/A')}"
                if metrics.get('cache_creation_input_tokens'):
                    metrics_text += f"\n• Токены создания кэша: {metrics.get('cache_creation_input_tokens')}"
                if metrics.get('cache_read_input_tokens'):
                    metrics_text += f"\n• Токены чтения кэша: {metrics.get('cache_read_input_tokens')}"
            else:
                metrics_text += f"• Промпт токены: {metrics.get('prompt_tokens', 'N/A')}\n"
                metrics_text += f"• Токены ответа: {metrics.get('completion_tokens', 'N/A')}\n"
                metrics_text += f"• Всего токенов: {metrics.get('total_tokens', 'N/A')}"
            
            reply_text += metrics_text
        
        # Отправляем ответ (разбиваем на части, если слишком длинный)
        if len(reply_text) > 4096:
            # Telegram ограничивает длину сообщения 4096 символами
            parts = [reply_text[i:i+4096] for i in range(0, len(reply_text), 4096)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(reply_text)
            
    except Exception as e:
        error_message = f"❌ Ошибка при обработке запроса: {str(e)}"
        await update.message.reply_text(error_message)


def main():
    """Основная функция для запуска бота"""
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv("TELEGRAM_BOT_KEY")
    
    if not bot_token:
        print("❌ Ошибка: TELEGRAM_BOT_KEY не найден в .env файле!")
        return
    
    try:
        # Регистрируем команды в боковой панели бота
        commands = [
            BotCommand("start", "Начать работу с ботом (открывает меню)"),
            BotCommand("menu", "Открыть главное меню"),
            BotCommand("model", "Выбрать модель AI"),
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
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Игнорируем старые обновления при запуске
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при работе бота: {str(e)}")
        print("Убедитесь, что только один экземпляр бота запущен!")


if __name__ == "__main__":
    main()

