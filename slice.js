const fs = require('fs');

// Фиксированные пути к файлам
const INPUT_FILE_PATH = 'input.txt';  // Файл, из которого извлекаются оценки
const OUTPUT_FILE_PATH = 'rating.txt'; // Файл, в который записываются оценки

/**
 * Извлекает общую оценку из текста в формате "X/10".
 * @param {string} text - Текст, содержащий оценку.
 * @returns {string|null} - Строка с оценкой в формате "X/10" или null, если оценка не найдена.
 */
function extractOverallRating(text) {
  const regex = /Общая оценка:\s*(\d+\/\d+)/;
  const match = text.match(regex);
  
  if (match && match[1]) {
    return match[1];
  }
  
  return null;
}

/**
 * Обрабатывает файл, извлекает оценку и записывает её в выходной файл.
 */
function processFile() {
  try {
    console.log(`Чтение из файла: ${INPUT_FILE_PATH}`);
    
    // Чтение входного файла
    const content = fs.readFileSync(INPUT_FILE_PATH, 'utf-8');
    
    // Извлечение оценки
    const rating = extractOverallRating(content);
    
    if (rating) {
      // Запись оценки в выходной файл
      fs.writeFileSync(OUTPUT_FILE_PATH, rating);
      console.log(`Оценка ${rating} успешно извлечена и записана в ${OUTPUT_FILE_PATH}`);
    } else {
      console.error('Оценка не найдена в тексте');
    }
  } catch (error) {
    console.error(`Ошибка при обработке файла: ${error.message}`);
  }
}

// Выполнение функции
processFile();