import os
import requests
from dotenv import load_dotenv

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

    Args:
        user_text (str): Текст, введенный пользователем
        first_prompt (str): Первый промпт для модели
        second_prompt (str): Второй промпт для проверки

    Returns:
        tuple: (first_model_response, second_model_response) - ответы моделей
    """
    # URL API Hugging Face для моделей
    model_url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

    # Отправка запроса к первой модели
    combined_text_first = f"{first_prompt}\n\n{user_text}"

    first_model_response = call_huggingface_api(
        model_url,
        combined_text_first,
        HF_API_KEY_FIRST
    )

    # Отправка запроса ко второй модели
    combined_text_second = f"{second_prompt}\n\nПользовательский ввод:\n{user_text}\n\nОтвет первой модели:\n{first_model_response}"

    second_model_response = call_huggingface_api(
        model_url,
        combined_text_second,
        HF_API_KEY_SECOND
    )

    return first_model_response, second_model_response

def call_huggingface_api(url, input_text, api_key):
    """
    Вызывает API Hugging Face для получения ответа от модели.

    Args:
        url (str): URL API Hugging Face
        input_text (str): Входной текст для модели
        api_key (str): API ключ для доступа к модели

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
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
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

    except Exception as e:
        print(f"Ошибка при вызове Hugging Face API: {str(e)}")
        return f"Ошибка при получении ответа от модели: {str(e)}"
        return f"Ошибка при получении ответа от модели: {str(e)}"