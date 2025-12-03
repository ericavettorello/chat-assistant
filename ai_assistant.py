# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic
from typing import List, Dict, Optional, Union

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Импортируем конфигурацию
from config import (
    PROXY_API_KEY,
    OPENAI_BASE_URL,
    ANTHROPIC_BASE_URL,
    PROXY_SUPPORTS_REASONING
)
from logger import log_error, log_request
import time

# Инициализируем клиент OpenAI с прокси-сервером
openai_client = OpenAI(
    api_key=PROXY_API_KEY,
    base_url=OPENAI_BASE_URL
)

# Инициализируем клиент Anthropic (Claude) с прокси-сервером
anthropic_client = Anthropic(
    api_key=PROXY_API_KEY,
    base_url=ANTHROPIC_BASE_URL
)


class ChatAssistant:
    """
    Класс для работы с Chat Completions API с поддержкой диалога.
    Сохраняет историю сообщений для поддержания контекста разговора.
    История сохраняется в файл для постоянного хранения.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", system_message: str = "Ты полезный ассистент.", 
                 history_file: Optional[str] = "chat_history.json", temperature: float = 1.0):
        """
        Инициализация ассистента.
        
        Args:
            model: Модель OpenAI для использования (по умолчанию gpt-3.5-turbo)
            system_message: Системное сообщение для настройки поведения ассистента
            history_file: Путь к файлу для сохранения истории (None - не сохранять в файл)
            temperature: Температура для генерации ответов (0.0-2.0, по умолчанию 1.0)
        """
        self.model = model
        self.history_file = history_file
        self.temperature = temperature
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_message}
        ]
        
        # Загружаем историю из файла, если она существует
        if self.history_file:
            self.load_history()
            # Если файла не было, сохраняем начальное состояние
            if not Path(self.history_file).exists():
                self.save_history()
    
    def add_message(self, role: str, content: str):
        """
        Добавляет сообщение в историю диалога и сохраняет в файл.
        
        Args:
            role: Роль отправителя ('user', 'assistant', 'system')
            content: Содержимое сообщения
        """
        self.messages.append({"role": role, "content": content})
        # Автоматически сохраняем после каждого сообщения
        if self.history_file:
            self.save_history()
    
    def is_claude_model(self) -> bool:
        """Проверяет, является ли модель Claude (Anthropic)"""
        claude_models = ["claude", "sonnet"]
        return any(model in self.model.lower() for model in claude_models)
    
    def get_response(self, user_message: str, reasoning_effort: Optional[str] = None, 
                     reasoning_summary: Optional[str] = None) -> tuple[str, Optional[Dict]]:
        """
        Отправляет сообщение пользователя и получает ответ от ассистента.
        Автоматически сохраняет оба сообщения в историю для поддержания контекста.
        
        Args:
            user_message: Сообщение от пользователя
            reasoning_effort: Уровень reasoning для self-reasoning моделей 
                             ('minimal', 'low', 'medium', 'high')
            reasoning_summary: Тип summary для reasoning ('auto', 'concise', 'detailed')
            
        Returns:
            tuple: (Ответ от ассистента, Метрики reasoning если доступны)
        """
        # Добавляем сообщение пользователя в историю
        self.add_message("user", user_message)
        
        reasoning_metrics = None
        
        try:
            if self.is_claude_model():
                # Работа с Claude (Anthropic)
                # Подготавливаем сообщения для Claude (формат отличается от OpenAI)
                claude_messages = []
                system_message = None
                
                for msg in self.messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    elif msg["role"] in ["user", "assistant"]:
                        claude_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                
                # Логируем параметры запроса
                request_params = {
                    "model": self.model,
                    "max_tokens": 4096,
                    "messages": claude_messages,
                    "system": system_message if system_message else None
                }
                
                # Засекаем время выполнения запроса
                start_time = time.time()
                
                # Отправляем запрос к Claude API
                response = anthropic_client.messages.create(**request_params)
                
                response_time = time.time() - start_time
                
                # Извлекаем ответ
                assistant_message = response.content[0].text
                
                # Извлекаем reasoning метрики, если доступны
                tokens_info = None
                if hasattr(response, 'usage') and response.usage:
                    reasoning_metrics = {
                        "input_tokens": getattr(response.usage, 'input_tokens', 0),
                        "output_tokens": getattr(response.usage, 'output_tokens', 0),
                        "cache_creation_input_tokens": getattr(response.usage, 'cache_creation_input_tokens', 0),
                        "cache_read_input_tokens": getattr(response.usage, 'cache_read_input_tokens', 0),
                    }
                    tokens_info = {
                        "input_tokens": reasoning_metrics["input_tokens"],
                        "output_tokens": reasoning_metrics["output_tokens"]
                    }
                
                # Проверяем наличие reasoning метрик в response
                if hasattr(response, 'stop_reason'):
                    reasoning_metrics = reasoning_metrics or {}
                    reasoning_metrics["stop_reason"] = response.stop_reason
                
                # Логируем успешный запрос
                log_request(
                    service="Anthropic",
                    model=self.model,
                    params=request_params,
                    response_time=response_time,
                    tokens=tokens_info
                )
                
            else:
                # Работа с OpenAI моделями
                # Подготавливаем параметры запроса
                request_params = {
                    "model": self.model,
                    "messages": self.messages,
                    "temperature": self.temperature
                }
                
                # Добавляем reasoning_effort для self-reasoning моделей (gpt-5, o-series)
                # ВАЖНО: Прокси-сервер api.proxyapi.ru не поддерживает reasoning_effort
                # Параметр передается только если прокси поддерживает reasoning
                if reasoning_effort and PROXY_SUPPORTS_REASONING:
                    request_params["reasoning_effort"] = reasoning_effort
                elif reasoning_effort and not PROXY_SUPPORTS_REASONING:
                    # Для прокси-сервера reasoning параметры игнорируются
                    # Модель все равно будет работать, но без специальных reasoning параметров
                    pass
                
                # Засекаем время выполнения запроса
                start_time = time.time()
                
                # Отправляем запрос к API
                response = openai_client.chat.completions.create(**request_params)
                
                response_time = time.time() - start_time
                
                # Извлекаем ответ ассистента
                assistant_message = response.choices[0].message.content
                
                # Извлекаем usage метрики
                tokens_info = None
                if hasattr(response, 'usage') and response.usage:
                    reasoning_metrics = {
                        "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                        "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                        "total_tokens": getattr(response.usage, 'total_tokens', 0),
                    }
                    tokens_info = {
                        "total_tokens": reasoning_metrics["total_tokens"],
                        "prompt_tokens": reasoning_metrics["prompt_tokens"],
                        "completion_tokens": reasoning_metrics["completion_tokens"]
                    }
                
                # Логируем успешный запрос
                log_request(
                    service="OpenAI",
                    model=self.model,
                    params=request_params,
                    response_time=response_time,
                    tokens=tokens_info
                )
            
            # Добавляем ответ ассистента в историю
            self.add_message("assistant", assistant_message)
            
            return assistant_message, reasoning_metrics
        
        except Exception as e:
            # Логируем ошибку с контекстом
            log_error(e, context={
                "model": self.model,
                "is_claude": self.is_claude_model(),
                "temperature": self.temperature,
                "messages_count": len(self.messages)
            })
            return f"Ошибка при получении ответа: {str(e)}", None
    
    def clear_history(self, keep_system: bool = True):
        """
        Очищает историю диалога.
        
        Args:
            keep_system: Если True, сохраняет системное сообщение
        """
        if keep_system:
            self.messages = [self.messages[0]]  # Оставляем только системное сообщение
        else:
            self.messages = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Возвращает полную историю диалога.
        
        Returns:
            Список всех сообщений в диалоге
        """
        return self.messages.copy()
    
    def save_history(self, language: str = None):
        """
        Сохраняет историю диалога в JSON файл.
        
        Args:
            language: Код языка для сохранения (опционально, если не указан, пытается получить из context_manager)
        """
        if not self.history_file:
            return
        
        try:
            # Если язык не передан, пытаемся получить его из context_manager по user_id из имени файла
            if language is None and self.history_file:
                try:
                    import re
                    from context_manager import get_user_language
                    # Извлекаем user_id из имени файла chat_history_{user_id}.json
                    match = re.search(r'chat_history_(\d+)\.json', self.history_file)
                    if match:
                        user_id = int(match.group(1))
                        language = get_user_language(user_id)
                except Exception:
                    pass  # Если не удалось получить язык, сохраняем без него
            
            history_data = {
                "model": self.model,
                "temperature": self.temperature,
                "last_updated": datetime.now().isoformat(),
                "messages": self.messages
            }
            
            # Добавляем язык, если он доступен
            if language:
                history_data["language"] = language
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(e, context={"action": "save_history", "file": self.history_file})
            print(f"Ошибка при сохранении истории: {str(e)}")
    
    
    def load_history(self):
        """
        Загружает историю диалога из JSON файла.
        
        Returns:
            str: Код языка из истории или None
        """
        if not self.history_file or not Path(self.history_file).exists():
            return None
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                # Загружаем сообщения, если они есть
                if "messages" in history_data and history_data["messages"]:
                    self.messages = history_data["messages"]
                # Обновляем модель, если она указана в файле
                if "model" in history_data:
                    self.model = history_data["model"]
                # Обновляем температуру, если она указана в файле
                if "temperature" in history_data:
                    self.temperature = history_data["temperature"]
                # Возвращаем язык, если он указан в файле
                return history_data.get("language")
        except Exception as e:
            log_error(e, context={"action": "load_history", "file": self.history_file})
            print(f"Ошибка при загрузке истории: {str(e)}")
            return None
    
    def export_history_to_text(self, output_file: str = "chat_history.txt"):
        """
        Экспортирует историю диалога в текстовый файл для удобного чтения.
        
        Args:
            output_file: Путь к выходному текстовому файлу
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== История диалога ===\n\n")
                for i, msg in enumerate(self.messages, 1):
                    role_name = {
                        "system": "Система",
                        "user": "Пользователь",
                        "assistant": "Ассистент"
                    }.get(msg["role"], msg["role"])
                    
                    f.write(f"{i}. [{role_name}]\n{msg['content']}\n\n")
                    f.write("-" * 50 + "\n\n")
            
            print(f"История экспортирована в файл: {output_file}")
        except Exception as e:
            log_error(e, context={"action": "export_history", "file": output_file})
            print(f"Ошибка при экспорте истории: {str(e)}")


def simple_chat(model: str = "gpt-3.5-turbo", system_message: str = "Ты полезный ассистент.") -> str:
    """
    Простая функция для однократного запроса без сохранения контекста.
    
    Args:
        model: Модель OpenAI для использования
        system_message: Системное сообщение
        
    Returns:
        Ответ от ассистента
    """
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": "Привет!"}
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {str(e)}"


# Интерактивный диалог
def interactive_chat():
    """
    Запускает интерактивный диалог с ассистентом.
    Пользователь может вводить сообщения, история сохраняется автоматически.
    """
    print("=== Интерактивный диалог с AI ассистентом ===\n")
    print("Доступные модели:")
    print("  OpenAI:")
    print("    - gpt-3.5-turbo (быстрая, стандартная)")
    print("    - gpt-4o (продвинутая)")
    print("    - gpt-5-pro (self-reasoning, высокий уровень reasoning)")
    print("    - o1, o3 (self-reasoning модели)")
    print("  Anthropic (Claude):")
    print("    - claude-sonnet-4-5-20250929 (Claude 4.5 Sonnet с reasoning метриками)")
    print()
    
    # Выбор модели
    model_choice = input("Выберите модель (Enter для claude-sonnet-4-5-20250929): ").strip()
    if not model_choice:
        model_choice = "claude-sonnet-4-5-20250929"
    
    # Настройка reasoning для self-reasoning моделей
    reasoning_models = ["gpt-5-pro", "gpt-5", "o1", "o3", "o1-preview", "o3-mini"]
    use_reasoning = any(model in model_choice.lower() for model in reasoning_models)
    
    reasoning_effort = None
    reasoning_summary = None
    
    if use_reasoning:
        print("\nНастройка self-reasoning:")
        if not PROXY_SUPPORTS_REASONING:
            print("⚠ Внимание: Прокси-сервер не поддерживает reasoning параметры.")
            print("Модель будет работать, но без специальных reasoning настроек.\n")
        effort_choice = input("Уровень reasoning effort (minimal/low/medium/high, Enter для high): ").strip()
        reasoning_effort = effort_choice if effort_choice else "high"
        reasoning_summary = None  # Не используется, так как может не поддерживаться прокси-сервером
    
    # Системное сообщение (используется значение по умолчанию)
    system_msg = "Ты дружелюбный и умный помощник. Отвечай подробно и полезно."
    
    # Создаем ассистента
    assistant = ChatAssistant(
        model=model_choice,
        system_message=system_msg
    )
    
    print(f"\n✓ Модель: {model_choice}")
    if assistant.is_claude_model():
        print("✓ Провайдер: Anthropic (Claude)")
        print("✓ Reasoning метрики будут отображаться после каждого ответа")
    else:
        print("✓ Провайдер: OpenAI")
    if use_reasoning:
        print(f"✓ Reasoning effort: {reasoning_effort}")
    print(f"✓ История сохраняется в: {assistant.history_file}")
    print("\n" + "="*60)
    print("Начните диалог! (введите 'exit' или 'quit' для выхода)")
    print("Команды: 'export' или 'save' - экспорт истории в текстовый файл")
    print("="*60 + "\n")
    
    # Основной цикл диалога
    while True:
        try:
            # Получаем сообщение от пользователя
            user_input = input("Вы: ").strip()
            
            # Проверка на выход
            if user_input.lower() in ['exit', 'quit', 'выход', 'стоп']:
                print("\n=== Завершение диалога ===")
                print(f"История сохранена в: {assistant.history_file}")
                break
            
            # Команда для экспорта истории в текстовый файл
            if user_input.lower() in ['export', 'экспорт', 'save', 'сохранить']:
                assistant.export_history_to_text("chat_history.txt")
                print("История экспортирована в: chat_history.txt\n")
                continue
            
            if not user_input:
                continue
            
            # Получаем ответ от ассистента
            print("\nАссистент думает...")
            if use_reasoning:
                response, metrics = assistant.get_response(
                    user_input, 
                    reasoning_effort=reasoning_effort
                )
            else:
                response, metrics = assistant.get_response(user_input)
            
            print(f"Ассистент: {response}\n")
            
            # Отображаем reasoning метрики, если доступны
            if metrics:
                print("📊 Reasoning метрики:")
                if assistant.is_claude_model():
                    print(f"   • Входные токены: {metrics.get('input_tokens', 'N/A')}")
                    print(f"   • Выходные токены: {metrics.get('output_tokens', 'N/A')}")
                    if metrics.get('cache_creation_input_tokens'):
                        print(f"   • Токены создания кэша: {metrics.get('cache_creation_input_tokens', 'N/A')}")
                    if metrics.get('cache_read_input_tokens'):
                        print(f"   • Токены чтения кэша: {metrics.get('cache_read_input_tokens', 'N/A')}")
                    if metrics.get('stop_reason'):
                        print(f"   • Причина остановки: {metrics.get('stop_reason', 'N/A')}")
                else:
                    print(f"   • Промпт токены: {metrics.get('prompt_tokens', 'N/A')}")
                    print(f"   • Токены ответа: {metrics.get('completion_tokens', 'N/A')}")
                    print(f"   • Всего токенов: {metrics.get('total_tokens', 'N/A')}")
                print()
            
            print("-" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n=== Прервано пользователем ===")
            print(f"История сохранена в: {assistant.history_file}")
            break
        except Exception as e:
            print(f"\nОшибка: {str(e)}\n")


# Пример использования
if __name__ == "__main__":
    # Запускаем интерактивный диалог
    interactive_chat()

