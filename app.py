from flask import Flask, request, jsonify, render_template
import os
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import json

# Импортируем модули обработки
from audio_processor import process_audio_file
from text_analyzer import analyze_text
from ai_detector import AIDetector

# Загружаем переменные окружения
load_dotenv()

# Инициализация Flask приложения
app = Flask(__name__)

# Настройка путей для загрузки файлов
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Инициализация детектора ИИ-текста
hf_token = os.environ.get("HUGGINGFACE_TOKEN")
try:
    ai_detector = AIDetector(model_name="blameitonthemoon/AI_detected", token=hf_token)
except Exception as e:
    print(f"Не удалось загрузить основную модель для детекции ИИ: {str(e)}")
    print("Использование альтернативной модели...")
    ai_detector = AIDetector(model_name="roberta-base-openai-detector")

# Загрузка промптов
def load_prompt(filename):
    with open(os.path.join('prompts', filename), 'r', encoding='utf-8') as f:
        return f.read()

try:
    first_prompt = load_prompt('prompt.txt')
    second_prompt = load_prompt('second_prompt.txt')
    print("Промпты успешно загружены")
except Exception as e:
    print(f"Ошибка при загрузке промптов: {str(e)}")
    first_prompt = ""
    second_prompt = ""

@app.route('/')
def index():
    """Отображение главной страницы."""
    return render_template('index.html')

@app.route('/analyze_text', methods=['POST'])
def analyze_text_route():
    """Обработка введенного пользователем текста."""
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({"error": "Текст не был предоставлен"}), 400

    user_text = data['text']

    try:
        # Анализируем текст с помощью модулей из AiText
        first_model_response, second_model_response = analyze_text(
            user_text,
            first_prompt,
            second_prompt
        )

        # Определяем вероятность ИИ-авторства введенного текста
        ai_probability = ai_detector.detect(user_text)
        human_probability = 100 - ai_probability

        return jsonify({
            "status": "success",
            "first_model_response": first_model_response,
            "second_model_response": second_model_response,
            "ai_probability": round(ai_probability, 1),
            "human_probability": round(human_probability, 1)
        })

    except Exception as e:
        import traceback
        print(f"Ошибка при анализе текста: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/process_audio', methods=['POST'])
def process_audio_route():
    """Обработка загруженного аудио или видео файла."""
    if 'file' not in request.files:
        return jsonify({"error": "Файл не был предоставлен"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    try:
        # Сохраняем файл с уникальным именем
        unique_id = uuid.uuid4().hex
        original_filename = secure_filename(file.filename)
        base_name, extension = os.path.splitext(original_filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_{unique_id}{extension}")
        file.save(file_path)

        # Обрабатываем аудио/видео файл и получаем транскрипцию
        transcription, txt_path = process_audio_file(file_path, ai_detector)

        # Анализируем полученный текст с помощью модулей из AiText
        first_model_response, second_model_response = analyze_text(
            transcription,
            first_prompt,
            second_prompt
        )

        return jsonify({
            "status": "success",
            "transcription": transcription,
            "first_model_response": first_model_response,
            "second_model_response": second_model_response,
            "file_path": txt_path
        })

    except Exception as e:
        import traceback
        print(f"Ошибка при обработке аудио: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)