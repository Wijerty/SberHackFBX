document.addEventListener('DOMContentLoaded', () => {
    // Tab switching logic
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and tab contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding tab content
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        });
    });

    // Text Analysis Form Submission
    const textForm = document.getElementById('text-form');
    const textResults = document.getElementById('text-results');

    textForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const textInput = document.getElementById('text-input');
        const textBlock = document.getElementById('text-analysis');

        // Show loading state
        textBlock.classList.add('loading');
        textResults.classList.add('hidden');

        try {
            const response = await fetch('/analyze_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: textInput.value })
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Update first and second model responses
                document.getElementById('first-model-response').textContent = data.first_model_response;
                document.getElementById('second-model-response').textContent = data.second_model_response;

                // Update AI and Human probability
                const aiProbabilityBar = document.getElementById('ai-probability-bar');
                const humanProbabilityBar = document.getElementById('human-probability-bar');
                const aiProbabilityText = document.getElementById('ai-probability-text');
                const humanProbabilityText = document.getElementById('human-probability-text');

                aiProbabilityBar.style.width = `${data.ai_probability}%`;
                humanProbabilityBar.style.width = `${data.human_probability}%`;
                aiProbabilityText.textContent = `${data.ai_probability}%`;
                humanProbabilityText.textContent = `${data.human_probability}%`;

                // Show results
                textResults.classList.remove('hidden');
            } else {
                alert(`Ошибка: ${data.error}`);
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при анализе текста');
        } finally {
            // Hide loading state
            textBlock.classList.remove('loading');
        }
    });

    // Audio/Video File Upload
    const audioInput = document.getElementById('audio-input');
    const fileChosen = document.getElementById('file-chosen');
    const audioForm = document.getElementById('audio-form');
    const audioResults = document.getElementById('audio-results');
    const audioBlock = document.getElementById('audio-analysis');

    // File selection display
    audioInput.addEventListener('change', () => {
        if (audioInput.files.length > 0) {
            fileChosen.textContent = audioInput.files[0].name;
        } else {
            fileChosen.textContent = 'Файл не выбран';
        }
    });

    // Audio/Video Form Submission
    audioForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Show loading state
        audioBlock.classList.add('loading');
        audioResults.classList.add('hidden');

        const formData = new FormData();
        formData.append('file', audioInput.files[0]);

        try {
            const response = await fetch('/process_audio', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Update transcription
                document.getElementById('transcription-text').textContent = data.transcription;

                // Update first and second model responses
                document.getElementById('audio-first-model-response').textContent = data.first_model_response;
                document.getElementById('audio-second-model-response').textContent = data.second_model_response;

                // Show results
                audioResults.classList.remove('hidden');
            } else {
                alert(`Ошибка: ${data.error}`);
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при обработке файла');
        } finally {
            // Hide loading state after 2 seconds to show animation
            setTimeout(() => {
                audioBlock.classList.remove('loading');
            }, 2000);
        }
    });
});