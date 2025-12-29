document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const attachBtn = document.getElementById('attach-btn');
    const fileInput = document.getElementById('file-input');

    // Welcome Message on Load
    setTimeout(() => addMessage("Hello! I am Gimi AI. Ready to chat or create images.", 'bot'), 500);

    // --- UPLOAD LOGIC ---
    attachBtn.addEventListener('click', () => fileInput.click()); 

    fileInput.addEventListener('change', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const loadingMsg = addMessage(`Uploading: ${file.name}...`, 'user');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload_file', { method: 'POST', body: formData });
            const data = await response.json();
            loadingMsg.remove();
            
            if (data.success) {
                addMessage(`📄 Document Analyzed: ${file.name}`, 'user');
                addMessage(data.message, 'bot');
            } else {
                addMessage("Upload Failed.", 'bot');
            }
        } catch (e) {
            loadingMsg.remove();
            addMessage("Error uploading file.", 'bot');
        }
        fileInput.value = '';
    });

    // --- CHAT LOGIC ---
    const addMessage = (content, sender, isImage = false, isLoading = false) => {
        const wrapperDiv = document.createElement('div');
        wrapperDiv.classList.add('message-wrapper', `${sender}-wrapper`);
        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('message-bubble', `${sender}-bubble`);
        if (isLoading) bubbleDiv.classList.add('loading');

        if (isImage) {
            const img = document.createElement('img');
            img.src = `data:image/jpeg;base64,${content}`;
            img.style.maxWidth = "100%";
            img.style.borderRadius = "10px";
            bubbleDiv.innerHTML = "Here is your image:<br>";
            bubbleDiv.appendChild(img);
        } else { 
            // Check if 'marked' library is available, else use plain text
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
        addMessage(command, 'user');
        userInput.value = '';
        const loadingBubble = addMessage("Thinking...", 'bot', false, true);

        try {
            const response = await fetch('/execute_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command, is_voice: isVoice }),
            });
            loadingBubble.parentElement.remove();
            const data = await response.json();

            if (data.is_image && data.image_data) addMessage(data.image_data, 'bot', true);
            else addMessage(data.response, 'bot', false);

            if (isVoice && data.has_audio) playAudio(data.audio_url);
        } catch (error) {
            loadingBubble.parentElement.remove();
            addMessage('Connection Error.', 'bot');
        }
    };

    // --- AUDIO LOGIC ---
    let currentAudio = null;
    const playAudio = (url) => {
        if(currentAudio) currentAudio.pause();
        currentAudio = new Audio(`${url}?t=${new Date().getTime()}`);
        currentAudio.play();
    };
    
    // Listeners
    sendBtn.addEventListener('click', () => { if(userInput.value.trim()) handleCommand(userInput.value.trim(), false); });
    userInput.addEventListener('keypress', (e) => { if(e.key==='Enter' && userInput.value.trim()) handleCommand(userInput.value.trim(), false); });
    
    // Mic Button Logic (Simple toggle)
    micBtn.addEventListener('click', () => {
         // Agar purana mic logic hai to yaha paste kar lena, 
         // warna filhal ye alert dega ki voice mode on hai.
         alert("Voice mode triggered (add your speech recognition code here)");
    });
});