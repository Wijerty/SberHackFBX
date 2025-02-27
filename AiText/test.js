import { HfInference } from "@huggingface/inference";

const HF_TOKEN = "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";
const inference = new HfInference(HF_TOKEN);

let message;

message = 'Привет! Отвечай на русском!';

async function main() {
  try {
    const response = await inference.chatCompletion({
      model: "google/gemma-2-2b-it",
      messages: [{ role: "user", content: message }],
      max_tokens: 512
    });
    
    console.log("Ответ от модели:");
    console.log(response.choices[0].message.content);
  } catch (error) {
    console.error("Произошла ошибка:");
    console.error(error);
  }
}

main();