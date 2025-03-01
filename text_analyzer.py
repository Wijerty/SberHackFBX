import os
import requests
from dotenv import load_dotenv
import time

# Загружаем переменные окружения
load_dotenv()

# Получаем API ключи для моделей Hugging Face из переменных окружения
HF_API_KEY_FIRST = os.environ.get("HF_API_KEY_FIRST", "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")  # Используем ключ из AiText
HF_API_KEY_SECOND = os.environ.get("HF_API_KEY_SECOND", "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")  # Используем ключ из AiText

def analyze_text(user_text, first_prompt, second_prompt):
    """
    Анализирует введенный пользователем текст, используя функциональность из AiText:
    1. Отправляет текст пользователя + первый промпт в первую модель
    2. Отправляет ответ первой модели + второй промпт во вторую модель
    3. Сбрасывает контекст после каждого запроса

    Args:
        user_text (str): Текст, введенный пользователем
        first_prompt (str): Первый промпт для модели
        second_prompt (str): Второй промпт для проверки

    Returns:
        tuple: (first_model_response, second_model_response) - ответы моделей
    """
    # URL API Hugging Face для моделей с параметром, сбрасывающим контекст
    model_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

    # Отправка запроса к первой модели
    combined_text_first = f"{first_prompt}\n\n{user_text}"

    first_model_response = call_huggingface_api(
        model_url,
        combined_text_first,
        HF_API_KEY_FIRST,
        reset_context=True  # Добавляем параметр сброса контекста
    )

    # Отправка запроса ко второй модели
    combined_text_second = f"{second_prompt}\n\nПользовательский ввод:\n{user_text}\n\nОтвет первой модели:\n{first_model_response}"

    second_model_response = call_huggingface_api(
        model_url,
        combined_text_second,
        HF_API_KEY_SECOND,
        reset_context=True  # Добавляем параметр сброса контекста
    )

    return first_model_response, second_model_response

def call_huggingface_api(url, input_text, api_key, max_retries=3, reset_context=False):
    """
    Вызывает API Hugging Face для получения ответа от модели с возможностью повторных попыток и сброса контекста.

    Args:
        url (str): URL API Hugging Face
        input_text (str): Входной текст для модели
        api_key (str): API ключ для доступа к модели
        max_retries (int): Максимальное количество повторных попыток
        reset_context (bool): Флаг для сброса предыдущего контекста

    Returns:
        str: Ответ модели
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": input_text,
        "parameters": {
            "max_tokens": 512,
            "return_full_text": False,
            "temperature": 0.7,  # Добавляем температуру для более стабильного ответа
            "timeout": 120,  # Увеличиваем таймаут до 2 минут
        }
    }

    # Добавляем параметр сброса контекста, если установлен флаг
    if reset_context:
        payload["parameters"]["reset_context"] = True

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=130)

            # Обработка специфических HTTP-кодов
            if response.status_code == 503:  # Service Unavailable
                print(f"Сервис недоступен. Повторная попытка {attempt + 1}")
                time.sleep(2 ** attempt)  # Экспоненциальная задержка
                continue

            response.raise_for_status()  # Проверяем статус ответа

            # Обрабатываем различные форматы ответа от Hugging Face
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                if "generated_text" in data[0]:
                    return data[0]["generated_text"]
                else:
                    return str(data[0])
            elif isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"]
            else:
                return str(data)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при вызове Hugging Face API (попытка {attempt + 1}): {str(e)}")

            # Добавляем exponential backoff
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                # Если все попытки исчерпаны
                error_message = f"Не удалось получить ответ от модели после {max_retries} попыток. Ошибка: {str(e)}"
                print(error_message)
                return error_message

    # Если все попытки неудачны
    return "Не удалось получить ответ от модели. Пожалуйста, попробуйте позже."