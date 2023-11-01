const toggleButton = document.getElementById('toggleRecording');
const transcriptionDiv = document.getElementById('transcription');
const responseDiv = document.getElementById('response');
const languageDiv = document.getElementById('language');
let mediaRecorder;
let audioChunks = [];
let language = 'ja-JP';
languageDiv.innerHTML = 'lang: '+ language;

toggleButton.addEventListener('click', async () => {
    const currentState = toggleButton.getAttribute('data-state');

    // Chrome will return an empty array if the first call is to an empty array.
    speechSynthesis.getVoices();
    if (currentState === 'inactive') {
        window.speechSynthesis.cancel();
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        /*
        Speech recognition ends when silence continues for a certain period of time
        */
        const options = {
            threshold: -50,
            interval: 150
        };
        const speechEvents = hark(stream, options);
        speechEvents.on('stopped_speaking', function () {
            console.log('stopped_speaking');
            speechEvents.off('stopped_speaking');
            mediaRecorder.stop();
            toggleButton.src = 'mic_disable.png';
            toggleButton.style.cursor = 'not-allowed';
        });

        speechEvents.on('speaking', function () {
            console.log('speaking');
        });

        /*
        Recording audio
        */
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob);

            const response = await fetch('/upload-audio', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            console.log(data);

            transcriptionDiv.innerHTML = data.transcription;
            responseDiv.innerHTML = data.response;

            const utterance = new SpeechSynthesisUtterance(data.response);
            console.log(`SpeechHandler.speakUtterance ${language}`)
            var voices = speechSynthesis.getVoices();

            utterance.lang = language;
            if (language == 'en-US') {
                //utterance.voice = voices[145]; // en-US:Google US English Female
                utterance.voice = voices.find(voice => voice.name === 'Google UK English Female');
                utterance.rate = 1.0;
                this.delimiter = this.delimitersDefault;
            } else if (language == 'zh-CN') {
                utterance.voice = voices[169]; // zh-CN: Google 普通話
                utterance.rate = 0.9;
                this.delimiters = this.delimitersDefault;
            } else if (language == 'ko-KR') {
                utterance.voice = voices[155];
                utterance.rate = 1.0;
                this.delimiters = this.delimitersDefault;
            } else {
                utterance.language = 'ja-JP';
                utterance.rate = 1.3;
            }
            window.speechSynthesis.speak(utterance);

            console.log(`SpeechHandler.speakUtterance ${utterance}`)
            toggleButton.src = 'mic_ready.png';
            toggleButton.setAttribute('data-state', 'inactive');
            toggleButton.style.cursor = 'pointer';
        };

        toggleButton.src = 'mic_recording.png';
        toggleButton.setAttribute('data-state', 'active');
        audioChunks = [];
        mediaRecorder.start();
    } else if (currentState === 'active') {
        /*
        Click to end voice recognition
        */
        mediaRecorder.stop();
        toggleButton.src = 'mic_disable.png';
        toggleButton.style.cursor = 'not-allowed';
    }
});

window.addEventListener('DOMContentLoaded', (event) => {
    // language
    window.addEventListener('keypress', (e) => {
        if (e.code === 'Space') {
            return
        }
        else if (e.code === 'KeyE') {
            language = 'en-US';
            lang_iso639 = 'en';
        }
        else if (e.code === 'KeyJ') {
            language = 'ja-JP';
            lang_iso639 = 'ja';
        }
        else if (e.code === 'KeyZ') {
            // https://segakuin.com/html/attribute/lang.html
            language = 'zh-CN';
            lang_iso639 = 'zh';
        }
        else if (e.code === 'KeyK') {
            language = 'ko-KR';
            lang_iso639 = 'ko';
        }
        languageDiv.innerHTML = 'lang: '+ language;

        const response = fetch(`/set?language=${lang_iso639}`, {
            method: 'GET',
        });
    });
});