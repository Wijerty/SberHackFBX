// Глобальные переменные для хранения данных
let savedText = "";
let fileText = ""; // Текст из первого файла
let secondFileText = ""; // Текст из второго файла
let firstModelResponse = ""; // Ответ от первой модели

// Функция для загрузки текста из файла при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM полностью загружен");
    
    // Добавляем обработчик событий для кнопки
    document.getElementById('submitButton').addEventListener('click', saveText);
    
    // Загружаем тексты из файлов
    loadTextFromFile();
    loadSecondTextFromFile();
});

// Функция для загрузки текста из первого файла
async function loadTextFromFile() {
    try {
        console.log("Загрузка текста из первого файла...");
        
        // Путь к файлу в проекте
        const filePath = './prompt.txt'; // Измените имя файла при необходимости
        
        // Загружаем содержимое файла
        const response = await fetch(filePath);
        
        if (!response.ok) {
            throw new Error(`Не удалось загрузить файл (статус: ${response.status})`);
        }
        
        // Получаем текст из файла
        fileText = await response.text();
        console.log("Текст из первого файла загружен:", fileText);
        
        // Обновляем статус загрузки на странице
        document.getElementById('fileStatus').textContent = 'Файл с инструкциями загружен успешно';
    } catch (error) {
        console.error("Ошибка при загрузке первого файла:", error);
        document.getElementById('fileStatus').textContent = 'Ошибка загрузки файла с инструкциями: ' + error.message;
    }
}

// Функция для загрузки текста из второго файла
async function loadSecondTextFromFile() {
    try {
        console.log("Загрузка текста из второго файла...");
        
        // Путь ко второму файлу в проекте
        const filePath = './second_prompt.txt'; // Имя второго файла
        
        // Загружаем содержимое файла
        const response = await fetch(filePath);
        
        if (!response.ok) {
            throw new Error(`Не удалось загрузить второй файл (статус: ${response.status})`);
        }
        
        // Получаем текст из файла
        secondFileText = await response.text();
        console.log("Текст из второго файла загружен:", secondFileText);
        
        // Обновляем статус загрузки на странице
        document.getElementById('secondFileStatus').textContent = 'Второй файл с инструкциями загружен успешно';
    } catch (error) {
        console.error("Ошибка при загрузке второго файла:", error);
        document.getElementById('secondFileStatus').textContent = 'Ошибка загрузки второго файла с инструкциями: ' + error.message;
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

// Основная функция для работы с первой моделью через fetch с поддержкой потокового ответа
async function main() {
    if (!savedText) {
        console.error("Текст не был сохранён!");
        return;
    }

    try {
        // Показываем сообщение о готовности получать ответ
        document.getElementById('modelOutput').innerHTML = '<strong>Ожидаем ответ первой модели:</strong><br>';
        
        // Создаем элемент для динамического вывода ответа
        const responseElement = document.createElement('div');
        responseElement.id = 'modelResponseText';
        document.getElementById('modelOutput').appendChild(responseElement);

        // Объединяем текст из файла и пользовательский ввод
        const combinedText = fileText ? fileText + "\n\n" + savedText : savedText;
        console.log("Отправляем в первую модель комбинированный текст:", combinedText);

        // URL API Hugging Face для первой модели
        const url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1";

        // Заголовки запроса
        const headers = {
            Authorization: `Bearer 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`, 
            "Content-Type": "application/json",
        };

        // Тело запроса с комбинированным текстом и включенным stream
        const payload = {
            inputs: combinedText,
            parameters: { 
                max_tokens: 512,
                return_full_text: false,
                stream: true // Включаем потоковую передачу
            },
        };

        console.log("Отправляем запрос на:", url);
        console.log("Данные запроса:", payload);

        // Отправляем POST-запрос
        const response = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload),
        });

        console.log("Получен ответ от API первой модели со статусом:", response.status);

        // Обработка ошибки
        if (!response.ok) {
            throw new Error(`Ошибка API: ${response.status} ${response.statusText}`);
        }

        // Проверяем, что ответ можно прочитать как поток
        if (response.body) {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedResponse = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                // Декодируем и обрабатываем полученный фрагмент
                const chunk = decoder.decode(value, { stream: true });
                console.log("Получен фрагмент от первой модели:", chunk);
                
                try {
                    // Hugging Face может отправлять данные в формате JSON
                    const jsonData = JSON.parse(chunk);
                    let textChunk = '';
                    
                    if (Array.isArray(jsonData)) {
                        textChunk = jsonData[0]?.generated_text || '';
                    } else {
                        textChunk = jsonData.generated_text || '';
                    }
                    
                    // Добавляем новый текст к уже полученному
                    accumulatedResponse += textChunk;
                } catch (e) {
                    // Если не удалось разобрать как JSON, просто добавляем как текст
                    console.log("Не удалось распарсить как JSON, добавляем как текст");
                    accumulatedResponse += chunk;
                }
                
                // Обновляем отображаемый текст
                document.getElementById('modelResponseText').textContent = accumulatedResponse;
            }
            
            // После завершения потока, если результат пустой
            if (!accumulatedResponse.trim()) {
                document.getElementById('modelResponseText').textContent = "Первая модель вернула пустой ответ. Попробуйте другой запрос.";
                firstModelResponse = "";
            } else {
                firstModelResponse = accumulatedResponse;
                console.log("Полный ответ от первой модели:", firstModelResponse);
            }
            
            // После получения ответа от первой модели вызываем вторую
            await callSecondModel();
            
        } else {
            // Если поток не поддерживается, читаем ответ как обычно
            const data = await response.json();
            console.log("Полный ответ от API первой модели:", data);

            // Проверяем различные форматы ответа от Hugging Face
            let modelResponse = "";
            
            if (Array.isArray(data)) {
                if (data[0] && typeof data[0].generated_text === 'string') {
                    modelResponse = data[0].generated_text;
                } else if (typeof data[0] === 'string') {
                    modelResponse = data[0];
                }
            } else if (data && typeof data.generated_text === 'string') {
                modelResponse = data.generated_text;
            } else {
                modelResponse = JSON.stringify(data);
            }

            // Если ответ получен, но он пустой
            if (!modelResponse || modelResponse.trim() === "") {
                modelResponse = "Первая модель вернула пустой ответ. Попробуйте другой запрос.";
                firstModelResponse = "";
            } else {
                firstModelResponse = modelResponse;
            }

            // Выводим ответ модели на страницу
            document.getElementById('modelResponseText').textContent = firstModelResponse;
            
            // После получения ответа от первой модели вызываем вторую
            await callSecondModel();
        }

    } catch (error) {
        console.error("Произошла ошибка при работе с первой моделью:", error);
        document.getElementById('modelOutput').innerHTML += '<strong>Ошибка:</strong> ' + error.message;
    }
}

// Функция для работы со второй моделью
async function callSecondModel() {
    try {
        // Создаем элемент для вывода ответа второй модели
        const secondModelOutputElement = document.createElement('div');
        secondModelOutputElement.id = 'secondModelOutput';
        secondModelOutputElement.innerHTML = '<strong>Ожидаем ответ второй модели:</strong><br>';
        document.getElementById('modelOutput').appendChild(secondModelOutputElement);

        // Создаем элемент для динамического вывода ответа
        const secondResponseElement = document.createElement('div');
        secondResponseElement.id = 'secondModelResponseText';
        secondModelOutputElement.appendChild(secondResponseElement);

        // Объединяем тексты для второй модели: второй файл + ввод пользователя + ответ первой модели
        const combinedTextForSecondModel = [
            secondFileText, 
            "Пользовательский ввод:", 
            savedText, 
            "Ответ первой модели:", 
            firstModelResponse
        ].filter(text => text).join("\n\n");
        
        console.log("Отправляем во вторую модель комбинированный текст:", combinedTextForSecondModel);

        // URL API Hugging Face для второй модели
        const url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"; // Можно указать другую модель

        // Заголовки запроса
        const headers = {
            Authorization: `Bearer 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`, 
            "Content-Type": "application/json",
        };

        // Тело запроса для второй модели
        const payload = {
            inputs: combinedTextForSecondModel,
            parameters: { 
                max_tokens: 512,
                return_full_text: false,
                stream: true
            },
        };

        console.log("Отправляем запрос ко второй модели на:", url);
        console.log("Данные запроса ко второй модели:", payload);

        // Отправляем POST-запрос
        const response = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload),
        });

        console.log("Получен ответ от API второй модели со статусом:", response.status);

        // Обработка ошибки
        if (!response.ok) {
            throw new Error(`Ошибка API второй модели: ${response.status} ${response.statusText}`);
        }

        // Переменная для хранения ответа второй модели
        let secondModelResponse = '';

        // Проверяем, что ответ можно прочитать как поток
        if (response.body) {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                // Декодируем и обрабатываем полученный фрагмент
                const chunk = decoder.decode(value, { stream: true });
                console.log("Получен фрагмент от второй модели:", chunk);
                
                try {
                    // Обработка JSON ответа
                    const jsonData = JSON.parse(chunk);
                    let textChunk = '';
                    
                    if (Array.isArray(jsonData)) {
                        textChunk = jsonData[0]?.generated_text || '';
                    } else {
                        textChunk = jsonData.generated_text || '';
                    }
                    
                    // Добавляем новый текст к уже полученному
                    secondModelResponse += textChunk;
                } catch (e) {
                    // Если не удалось разобрать как JSON, просто добавляем как текст
                    console.log("Не удалось распарсить как JSON, добавляем как текст");
                    secondModelResponse += chunk;
                }
                
                // Обновляем отображаемый текст
                document.getElementById('secondModelResponseText').textContent = secondModelResponse;
            }
            
            // После завершения потока
            if (!secondModelResponse.trim()) {
                secondModelResponse = "Вторая модель вернула пустой ответ. Попробуйте другой запрос.";
            }
            
        } else {
            // Если поток не поддерживается, читаем ответ как обычно
            const data = await response.json();
            console.log("Полный ответ от API второй модели:", data);

            // Проверяем различные форматы ответа от Hugging Face
            if (Array.isArray(data)) {
                if (data[0] && typeof data[0].generated_text === 'string') {
                    secondModelResponse = data[0].generated_text;
                } else if (typeof data[0] === 'string') {
                    secondModelResponse = data[0];
                }
            } else if (data && typeof data.generated_text === 'string') {
                secondModelResponse = data.generated_text;
            } else {
                secondModelResponse = JSON.stringify(data);
            }

            // Если ответ получен, но он пустой
            if (!secondModelResponse || secondModelResponse.trim() === "") {
                secondModelResponse = "Вторая модель вернула пустой ответ. Попробуйте другой запрос.";
            }

            // Выводим ответ модели на страницу
            document.getElementById('secondModelResponseText').textContent = secondModelResponse;
        }
        
        // Выводим ответ второй модели в консоль
        console.log("ИТОГОВЫЙ ОТВЕТ ВТОРОЙ МОДЕЛИ:", secondModelResponse);
        
        // Возвращаем ответ второй модели
        return secondModelResponse;

    } catch (error) {
        console.error("Произошла ошибка при работе со второй моделью:", error);
        document.getElementById('secondModelOutput').innerHTML += '<strong>Ошибка:</strong> ' + error.message;
        return null;
    }
}