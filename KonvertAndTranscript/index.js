const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

// Получаем аргументы командной строки
const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
    console.error("Usage: node index.js <inputPath> <outputPath>");
    process.exit(1);
}

// Проверяем, существует ли входной файл
if (!fs.existsSync(inputPath)) {
    console.error(`Input file not found: ${inputPath}`);
    process.exit(1);
}

console.log(`Converting file: ${inputPath}`);
console.log(`Output will be saved to: ${outputPath}`);

// Команда для конвертации видео в аудио
const command = `ffmpeg -i "${inputPath}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "${outputPath}"`;

exec(command, (error, stdout, stderr) => {
    if (error) {
        console.error(`Convert Error: ${error.message}`);
        console.error(`STDERR: ${stderr}`);
        process.exit(1);
    } else {
        console.log(`File converted successfully. Output saved to: ${outputPath}`);
        process.exit(0);
    }
});