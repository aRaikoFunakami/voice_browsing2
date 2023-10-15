const toggleButton = document.getElementById('toggleRecording');
const transcriptionDiv = document.getElementById('transcription');
let mediaRecorder;
let audioChunks = [];

toggleButton.addEventListener('click', async () => {
    const currentState = toggleButton.getAttribute('data-state');

    if (currentState === 'inactive') {
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
