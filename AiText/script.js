// Глобальная переменная для хранения сохраненного текста
let savedText = "";
let fileText = ""; // Переменная для хранения текста из файла

// Функция для загрузки текста из файла при загрузке страницы
document.addEventListener('DOMContentLoaded', loadTextFromFile);

// Функция для загрузки текста из файла
async function loadTextFromFile() {
    try {
        console.log("Загрузка текста из файла...");
        
        // Путь к файлу в проекте
        const filePath = './prompt.txt'; // Измените имя файла при необходимости
        
        // Загружаем содержимое файла
        const response = await fetch(filePath);
        
        if (!response.ok) {
            throw new Error(`Не удалось загрузить файл (статус: ${response.status})`);
        }
        
        // Получаем текст из файла
        fileText = await response.text();
        console.log("Текст из файла загружен:", fileText);
        
        // Обновляем статус загрузки на странице
        document.getElementById('fileStatus').textContent = 'Файл с инструкциями загружен успешно';
    } catch (error) {
        console.error("Ошибка при загрузке файла:", error);
        document.getElementById('fileStatus').textContent = 'Ошибка загрузки файла с инструкциями';
    }
}

// Функция для сохранения текста из поля ввода в переменную
function saveText() {
    console.log("Функция saveText была вызвана");

    // Получаем значение из поля ввода
    const userInput = document.getElementById('textInput').value.trim();
    console.log("Введённый текст:", userInput);

    if (!userInput) {
        console.error("Поле ввода пустое!");
        alert("Пожалуйста, введите текст.");
        return;
    }

    // Сохраняем текст в глобальную переменную
    savedText = userInput;
    console.log("Текст сохранён в переменную savedText:", savedText);

    // Выводим сохраненный текст на страницу
    document.getElementById('output').textContent = 'Сохраненный текст: ' + savedText;

    // Вызываем функцию main() после сохранения текста
    main();
}

// Основная функция для работы с моделью через fetch
async function main() {
    if (!savedText) {
        console.error("Текст не был сохранён!");
        return;
    }

    if (!fileText) {
        console.warn("Предупреждение: файл с инструкциями не был загружен!");
        alert("Файл с инструкциями не загружен. Продолжить без инструкций?");
        // Можно добавить код для повторной попытки загрузки файла
    }

    try {
        // Показываем сообщение о загрузке
        document.getElementById('modelOutput').innerHTML = '<strong>Загрузка...</strong>';

        // Объединяем текст из файла и пользовательский ввод
        // Файл идет первым как инструкции/контекст, затем пользовательский запрос
        const combinedText = fileText + "\n\n" + savedText;
        console.log("Отправляем в модель комбинированный текст:", combinedText);

        // URL API Hugging Face
        const url = "https://api-inference.huggingface.co/models/Qwen/QwQ-32B-Preview";

        // Заголовки запроса
        const headers = {
            Authorization: `Bearer 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`, 
            "Content-Type": "application/json",
        };

        // Тело запроса с комбинированным текстом
        const payload = {
            inputs: combinedText,
            parameters: { max_tokens: 512 },
        };

        // Отправляем POST-запрос
        const response = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload),
        });

        // Обработка ответа
        if (!response.ok) {
            throw new Error(`Ошибка API: ${response.status}`);
        }

        const data = await response.json();
        console.log("Полный ответ от API:", data);

        // Извлекаем сгенерированный текст
        const modelResponse = data[0]?.generated_text || "Ответ отсутствует";

        // Выводим ответ модели на страницу
        document.getElementById('modelOutput').innerHTML = '<strong>Ответ модели:</strong> ' + modelResponse;
    } catch (error) {
        console.error("Произошла ошибка при работе с моделью:");
        console.error(error);
        document.getElementById('modelOutput').innerHTML = '<strong>Ошибка:</strong> Не удалось получить ответ от модели.';
    }
}