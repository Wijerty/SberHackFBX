from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import numpy as np
import os
from huggingface_hub import login


class AIDetector:
    def __init__(self, model_name="blameitonthemoon/AI_detected", token=None):
        """
        Инициализация детектора ИИ-генерированного текста.
        Args:
            model_name: Название модели из Hugging Face для определения ИИ-текста
            token: Токен для аутентификации в Hugging Face Hub
        """
        try:
            print(f"Загрузка модели детекции ИИ: {model_name}")

            # Используем токен из аргумента, переменной окружения или запрашиваем у пользователя
            if token:
                # Если токен передан как аргумент
                hf_token = token
            elif "HUGGINGFACE_TOKEN" in os.environ:
                # Если токен указан в переменной окружения
                hf_token = os.environ.get("HUGGINGFACE_TOKEN")
            else:
                # Если модель требует аутентификации, но токен не предоставлен
                print("Модель требует аутентификации в Hugging Face Hub.")
                print(
                    "Используйте общедоступную модель или предоставьте токен через аргумент или переменную окружения HUGGINGFACE_TOKEN")

                # Попробуем использовать альтернативную модель
                print("Попытка использовать альтернативную публичную модель для детекции ИИ...")
                model_name = "roberta-base-openai-detector"  # Пример общедоступной модели
                hf_token = None

            # Логин в Hugging Face Hub, если есть токен
            if hf_token:
                print("Выполняем вход в Hugging Face Hub...")
                login(token=hf_token)

            # Загрузка модели и токенизатора
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            print(f"Модель детекции ИИ успешно загружена (устройство: {self.device})")
        except Exception as e:
            print(f"Ошибка при загрузке модели детекции ИИ: {str(e)}")
            raise

    def detect(self, text, chunk_size=512):
        """
        Определение вероятности того, что текст написан ИИ.

        Args:
            text: Текст для анализа
            chunk_size: Размер чанка для обработки длинных текстов

        Returns:
            float: Вероятность ИИ-авторства
        """
        try:
            # Для коротких текстов
            if len(text.split()) < 100:
                return self._process_text(text)

            # Для длинных текстов разбиваем на чанки
            chunks = self._split_text_into_chunks(text, chunk_size)
            probabilities = []

            for chunk in chunks:
                if chunk.strip():  # Пропускаем пустые чанки
                    prob = self._process_text(chunk)
                    probabilities.append(prob)

            # Возвращаем среднее значение вероятностей
            if probabilities:
                return sum(probabilities) / len(probabilities)
            else:
                return 0.0

        except Exception as e:
            print(f"Ошибка при определении авторства текста: {str(e)}")
            return 0.0