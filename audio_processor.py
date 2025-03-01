import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import os
import subprocess
import uuid
import warnings

# Скрываем предупреждения FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

# Определение устройства (GPU или CPU)
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Загружаем модель для транскрибации только один раз
def load_whisper_model():
    print("Загрузка модели Whisper для транскрибации...")
    # ID модели Whisper large-v3-turbo
    model_id = "openai/whisper-large-v3-turbo"

    # Загрузка модели с использованием Accelerate
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True
    )
    model.to(device)

    # Загрузка процессора
    processor = AutoProcessor.from_pretrained(model_id)

    # Создаем пайплайн для транскрибации с правильными параметрами
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=30,
        batch_size=8,  # Уменьшаем batch_size для экономии памяти
        return_timestamps=True,
        device=device,
    )

    return pipe

# Загружаем модель для транскрибации (инициализация происходит при импорте)
try:
    whisper_pipe = load_whisper_model()
    print("Модель Whisper успешно загружена")
except Exception as e:
    print(f"Ошибка при загрузке модели Whisper: {str(e)}")
    whisper_pipe = None

def process_audio_file(file_path, ai_detector):
    """
    Обрабатывает аудио или видео файл, конвертирует видео в аудио если нужно,
    выполняет транскрибацию и определяет авторство.

    Args:
        file_path (str): Путь к загруженному файлу
        ai_detector: Экземпляр класса для определения авторства текста

    Returns:
        tuple: (transcription, txt_path) - транскрибированный текст и путь к сохраненному файлу
    """
    print(f"Начало обработки файла: {file_path}")

    base_name, extension = os.path.splitext(file_path)

    # Проверяем тип файла (аудио или видео)
    if extension.lower() in ['.mp4', '.avi', '.mkv', '.mov']:  # Видео файлы
        # Конвертируем видео в аудио через ffmpeg напрямую
        converted_audio_path = f"{base_name}_converted.wav"

        # Используем ffmpeg для конвертации видео в аудио с флагом -y для автоматической перезаписи
        ffmpeg_cmd = f'ffmpeg -y -i "{file_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{converted_audio_path}"'
        print(f"Запуск команды: {ffmpeg_cmd}")
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        print(f"Видео успешно конвертировано в аудио: {converted_audio_path}")
        os.remove(file_path)  # Удаляем оригинальный видео файл
        file_path = converted_audio_path  # Используем конвертированный аудио файл
    elif extension.lower() not in ['.wav', '.mp3', '.flac', '.ogg']:  # Неподдерживаемые форматы
        raise ValueError("Неподдерживаемый формат файла. Пожалуйста, загрузите аудио или видео файлы.")

    # Проверка на наличие модели для транскрибации
    if whisper_pipe is None:
        raise ValueError("Модель Whisper не была инициализирована корректно")

    # Обработка аудио файла
    print(f"Начинаем транскрибацию файла: {file_path}")

    # Корректно используем параметры для языка русский
    result = whisper_pipe(
        file_path,
        generate_kwargs={
            "language": "ru",  # язык
            "task": "transcribe",  # явно указываем задачу транскрибации
        },
        chunk_length_s=30  # можно переопределить для конкретных файлов
    )

    # Извлекаем текст
    if isinstance(result, dict) and "text" in result:
        transcription = result["text"]
    else:
        # Обработка случая, когда результат - список чанков
        chunks = result
        transcription = " ".join([chunk["text"] for chunk in chunks]) if isinstance(chunks, list) else str(chunks)

    print(f"Транскрибация завершена. Длина текста: {len(transcription)} символов")

    # Определяем вероятность ИИ-авторства
    print("Определение авторства текста (человек/ИИ)...")
    ai_probability = ai_detector.detect(transcription)
    human_probability = 100 - ai_probability

    print(f"Результат определения авторства: ИИ: {ai_probability:.1f}%, Человек: {human_probability:.1f}%")

    # Сохраняем результат в текстовый файл
    txt_path = f"{base_name}_transcription.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(transcription)
        f.write("\n\n")
        f.write(f"Вероятность авторства: ИИ: {ai_probability:.1f}%, Человек: {human_probability:.1f}%")

    print(f"Результат сохранен в файл: {txt_path}")

    return transcription, txt_path