document.addEventListener('DOMContentLoaded', () => {
    // --- ELEMENTS ---
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const attachBtn = document.getElementById('attach-btn');
    const fileInput = document.getElementById('file-input');
    const audioPlayer = document.getElementById('ai-voice-player');
    
    // Status Elements
    const clockEl = document.getElementById('clock');
    const batteryLevelEl = document.getElementById('battery-level');
    const batteryIconEl = document.getElementById('battery-icon');

    // --- 1. REAL TIME CLOCK LOGIC ---
    function updateClock() {
        const now = new Date();
        let hours = now.getHours();
        let minutes = now.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // 0 ko 12 banana
        minutes = minutes < 10 ? '0' + minutes : minutes;
        clockEl.innerText = `${hours}:${minutes} ${ampm}`;
    }
    setInterval(updateClock, 1000);
    updateClock(); // Initial Call

    // --- 2. BATTERY STATUS LOGIC ---
    if ('getBattery' in navigator) {
        navigator.getBattery().then(function(battery) {
            function updateBattery() {
                const level = Math.round(battery.level * 100);
                batteryLevelEl.innerText = `${level}%`;
                
                // Icon Change Logic
                batteryIconEl.className = "fa-solid"; // Reset
                if(battery.charging) {
                    batteryIconEl.classList.add("fa-bolt"); // Charging Icon
                } else if(level > 75) {
                    batteryIconEl.classList.add("fa-battery-full");
                } else if(level > 50) {
                    batteryIconEl.classList.add("fa-battery-three-quarters");
                } else if(level > 25) {
                    batteryIconEl.classList.add("fa-battery-half");
                } else {
                    batteryIconEl.classList.add("fa-battery-quarter");
                    batteryIconEl.style.color = "red";
                }
            }
            updateBattery();
            battery.addEventListener('levelchange', updateBattery);
            battery.addEventListener('chargingchange', updateBattery);
        });
    } else {
        // Agar browser support na kare
        batteryLevelEl.style.display = 'none';
    }

    // --- 3. SPEECH RECOGNITION (MIC) LOGIC ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false; // Ek sentence ke baad stop
        recognition.lang = 'en-IN'; // Hinglish accent pakdega
        recognition.interimResults = false;

        micBtn.addEventListener('click', () => {
            if (micBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                recognition.start();
                micBtn.classList.add('listening');
                userInput.placeholder = "Listening...";
            }
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            micBtn.classList.remove('listening');
            userInput.placeholder = "Message...";
            // Auto Send after speaking
            handleCommand(transcript, true); 
        };

        recognition.onerror = () => {
            micBtn.classList.remove('listening');
            userInput.placeholder = "Message...";
        };
        
        recognition.onend = () => {
             micBtn.classList.remove('listening');
             userInput.placeholder = "Message...";
        };
    } else {
        micBtn.style.display = "none"; // Hide if browser not supported
        console.log("Speech API not supported");
    }

    // --- 4. CHAT & AUDIO LOGIC ---
    const addMessage = (content, sender, isImage = false, isLoading = false) => {
        const wrapperDiv = document.createElement('div');
        wrapperDiv.classList.add('message-wrapper', `${sender}-wrapper`);
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('message-bubble', `${sender}-bubble`);
        if (isLoading) bubbleDiv.classList.add('loading');

        if (isImage) {
            // ... (Image logic same as before) ...
            bubbleDiv.innerHTML = "Image generated."; 
        } else {
            // Markdown Parsing
            if (typeof marked !== 'undefined') {
                bubbleDiv.innerHTML = marked.parse(content);
            } else {
                bubbleDiv.innerText = content;
            }
        }
        
        wrapperDiv.appendChild(bubbleDiv);
        chatBox.appendChild(wrapperDiv);
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
        return bubbleDiv;
    };

    const handleCommand = async (command, isVoice) => {
        if(!command) return;
        
        // UI Updates
        addMessage(command, 'user');
        userInput.value = '';
        const loadingBubble = addMessage("Thinking...", 'bot', false, true);

        try {
            const response = await fetch('/execute_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command, is_voice: isVoice }),
            });
            
            const data = await response.json();
            loadingBubble.parentElement.remove(); // Remove loading

            // Show Text Response
            addMessage(data.response, 'bot');

            // Play Audio if Voice Mode
            if (isVoice && data.has_audio && data.audio_base64) {
                playBase64Audio(data.audio_base64);
            }

        } catch (error) {
            loadingBubble.parentElement.remove();
            addMessage('Connection Error.', 'bot');
        }
    };

    // --- PLAY BASE64 AUDIO ---
    function playBase64Audio(base64String) {
        audioPlayer.src = "data:audio/mp3;base64," + base64String;
        audioPlayer.play().catch(e => console.log("Audio Play Error:", e));
    }

    // --- EVENT LISTENERS ---
    sendBtn.addEventListener('click', () => handleCommand(userInput.value.trim(), false));
    userInput.addEventListener('keypress', (e) => { 
        if(e.key==='Enter') handleCommand(userInput.value.trim(), false); 
    });

    // File Upload Button
    attachBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', async () => {
        // ... (Keep your existing file upload logic here) ...
        const file = fileInput.files[0];
        if (!file) return;
        const loadingMsg = addMessage(`Uploading: ${file.name}...`, 'user');
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch('/upload_file', { method: 'POST', body: formData });
            const data = await res.json();
            loadingMsg.remove();
            if (data.success) {
                addMessage(`Uploaded: ${file.name}`, 'user');
                addMessage(data.message, 'bot');
            } else { addMessage("Upload Failed", 'bot'); }
        } catch(e) { loadingMsg.remove(); addMessage("Error", 'bot'); }
        fileInput.value = '';
    });
});
        
