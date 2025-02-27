from flask import Flask, request, jsonify
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
import librosa
import os

# Инициализация Flask приложения
app = Flask(__name__)

# Проверка наличия GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# ID модели Whisper large-v3-turbo
model_id = "openai/whisper-large-v3-turbo"

# Загрузка модели на GPU с half-precision
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.float16,  # Используем half-precision
    low_cpu_mem_usage=True,
    use_safetensors=True
)
model.to(device)

# Загрузка процессора
processor = AutoProcessor.from_pretrained(model_id)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Сохраняем файл во временную директорию
        upload_dir = "public/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)

        # Чтение аудио файла
        audio_data, sr = librosa.load(file_path, sr=16000)  # Whisper работает с частотой дискретизации 16kHz

        # Создание input_features и attention_mask
        inputs = processor(audio_data, sampling_rate=sr, return_tensors="pt", padding=True)

        # Преобразуем данные в torch.float16 и перемещаем на GPU
        inputs["input_features"] = inputs["input_features"].to(torch.float16).to(device)
        inputs["attention_mask"] = inputs["attention_mask"].to(torch.float16).to(device)

        print("Starting transcription...")

        # Выполнение транскрибации с использованием autocast
        with torch.cuda.amp.autocast():  # Автоматическое управление точностью
            predicted_ids = model.generate(
                inputs["input_features"],
                attention_mask=inputs["attention_mask"],
                language="ru"
            )
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

        print(f"Transcription result: {transcription}")

        # Удаляем временные файлы
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"status": "success", "message": "Транскрибация завершена.", "transcription": transcription})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)