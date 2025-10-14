// דוגמה איך לשלוח קובץ שמע מהקליינט לשרת

// 1. HTML - כפתור להקלטה ועליית קובץ
/*
<input type="file" id="audioFile" accept="audio/*">
<button onclick="uploadAudio()">שלח קובץ שמע</button>
<button onclick="startRecording()">התחל הקלטה</button>
<button onclick="stopRecording()">עצור הקלטה</button>
*/

// 2. JavaScript לטיפול בקבצים ושליחה לשרת

let mediaRecorder;
let audioChunks = [];

// הקלטה חיה
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendAudioToServer(audioBlob);
        };
        
        mediaRecorder.start();
        console.log('🎙️ Recording started...');
    } catch (error) {
        console.error('Error accessing microphone:', error);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        console.log('⏹️ Recording stopped');
    }
}

// שליחת קובץ שנבחר
async function uploadAudio() {
    const fileInput = document.getElementById('audioFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('אנא בחר קובץ שמע');
        return;
    }
    
    await sendAudioToServer(file);
}

// הפונקציה ששולחת לשרת
async function sendAudioToServer(audioBlob) {
    try {
        // יצירת FormData (multipart/form-data)
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'audio.wav');
        
        // קבלת token מ-localStorage
        const token = localStorage.getItem('authToken');
        
        console.log('🔊 Sending audio to server...');
        
        // שליחה לשרת
        const response = await fetch('http://localhost:8002/voice-query', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
                // אין Content-Type - נותנים לדפדפן לקבוע אוטומטית עם boundary
            },
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Server error');
        }
        
        // קבלת התגובה
        const result = await response.json();
        
        console.log('✅ Response from server:', result);
        
        // הצגת התוצאה למשתמש
        displayResult(result);
        
    } catch (error) {
        console.error('❌ Error sending audio:', error);
        alert(`שגיאה: ${error.message}`);
    }
}

// הצגת התוצאה
function displayResult(result) {
    const resultDiv = document.getElementById('result');
    
    resultDiv.innerHTML = `
        <div class="voice-result">
            <h3>🎙️ תמלול השמע:</h3>
            <p class="transcription">${result.question}</p>
            
            <h3>🤖 תשובת הצ'אטבוט:</h3>
            <p class="answer">${result.answer}</p>
            
            ${result.sql ? `
                <h3>📊 שאילתת SQL:</h3>
                <pre class="sql">${result.sql}</pre>
            ` : ''}
            
            ${result.data ? `
                <h3>📈 נתונים:</h3>
                <pre class="data">${JSON.stringify(result.data, null, 2)}</pre>
            ` : ''}
        </div>
    `;
}