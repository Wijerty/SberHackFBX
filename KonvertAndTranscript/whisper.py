from flask import Flask, request, jsonify, render_template
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import librosa
import numpy as np
import os
import subprocess
import tempfile
import uuid
from werkzeug.utils import secure_filename
import warnings

# Скрываем предупреждения FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

# Инициализация Flask приложения
app = Flask(__name__)

# Определение устройства (GPU или CPU)
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

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


@app.route('/')
def index():
    """Отображение главной страницы."""
    return render_template('index.html')


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Обработка загруженного файла (аудио или видео) и выполнение транскрибации."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Создаем временную директорию
        upload_dir = "public/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Используем уникальный идентификатор для избежания конфликтов имен файлов
        unique_id = uuid.uuid4().hex
        original_filename = secure_filename(file.filename)
        base_name, extension = os.path.splitext(original_filename)
        file_path = os.path.join(upload_dir, f"{base_name}_{unique_id}{extension}")
        file.save(file_path)

        # Проверяем тип файла (аудио или видео)
        if extension.lower() in ['.mp4', '.avi', '.mkv', '.mov']:  # Видео файлы
            # Конвертируем видео в аудио через ffmpeg напрямую
            converted_audio_path = os.path.join(upload_dir, f"{base_name}_{unique_id}_converted.wav")

            # Используем ffmpeg для конвертации видео в аудио с флагом -y для автоматической перезаписи
            ffmpeg_cmd = f'ffmpeg -y -i "{file_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{converted_audio_path}"'
            print(f"Запуск команды: {ffmpeg_cmd}")
            subprocess.run(ffmpeg_cmd, shell=True, check=True)

            print(f"Видео успешно конвертировано в аудио: {converted_audio_path}")
            os.remove(file_path)  # Удаляем оригинальный видео файл
            file_path = converted_audio_path  # Используем конвертированный аудио файл
        elif extension.lower() not in ['.wav', '.mp3', '.flac', '.ogg']:  # Неподдерживаемые форматы
            return jsonify({"error": "Unsupported file format. Please upload audio or video files."}), 400

        # Обработка аудио файлов
        print(f"Начинаем транскрибацию файла: {file_path}")

        # Корректно используем параметры для языка русский без конфликта с forced_decoder_ids
        # Измените этот участок в вашей функции transcribe (примерно строка 100)
        result = pipe(
            file_path,
            generate_kwargs={
                "language": "en",  # язык
                "task": "transcribe",  # явно укажите задачу транскрибации
                # Удалите строку ниже, которая вызывает ошибку
                # "condition_on_previous_text": True,
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

        # Вывод транскрибации в консоль и сохранение в файл
        print(f"Транскрибация завершена. Длина текста: {len(transcription)} символов")

        # Сохраняем результат в текстовый файл
        txt_path = os.path.splitext(file_path)[0] + "_transcription.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcription)

        print(f"Результат сохранен в файл: {txt_path}")

        # Возвращаем результат клиенту
        return jsonify({
            "status": "success",
            "message": "Транскрибация успешно завершена",
            "transcription": transcription,
            "file_path": txt_path
        })

    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    finally:
        # Очистка временных файлов при необходимости
        pass


if __name__ == '__main__':
    app.run(debug=True)