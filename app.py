import os
import asyncio
import edge_tts
import re
import requests 
import random
import time
import base64
import io
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__, template_folder='Frontend', static_folder='Frontend')
CORS(app)

UPLOAD_FOLDER = os.path.join('Frontend', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API Keys Setup (Environment Variable se uthayega)
gemini_keys = [os.getenv("GEMINI_API_KEY_1"), os.getenv("GEMINI_API_KEY_2"), os.getenv("GEMINI_API_KEY_3")]
current_gemini_index = 0
# Voice: Indian English Female (Change if needed)
VOICE = "en-IN-NeerjaNeural"

# Configure Gemini
def configure_genai():
    global current_gemini_index
    if current_gemini_index < len(gemini_keys) and gemini_keys[current_gemini_index]:
        genai.configure(api_key=gemini_keys[current_gemini_index])
    else:
        print("❌ No valid Gemini keys found.")
configure_genai()

# Main Chat Model
model = genai.GenerativeModel('models/gemini-2.5-flash-lite', 
                              system_instruction="You are Gimi AI. You are helpful, funny, and smart. Answer in Hinglish. Remember previous context and files uploaded by user.")
chat_session = model.start_chat(history=[])
prompt_model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

# --- Helper Functions ---

def remove_markdown(text): 
    # Clean text for TTS (Remove * # and extra spaces)
    return re.sub(' +', ' ', text.replace('*', '').replace('#', '').replace('_', '')).strip()

def get_gemini_response(prompt, is_voice=False):
    global current_gemini_index, chat_session, model
    try:
        # Chat Session use karne se purani baatein yaad rehti hain
        return chat_session.send_message(prompt).text
    except Exception as e:
        print(f"Gemini Error: {e}")
        # Retry Logic (Key Rotation)
        if current_gemini_index < len(gemini_keys) - 1:
            current_gemini_index += 1
            configure_genai()
            chat_session = model.start_chat(history=chat_session.history)
            try: return chat_session.send_message(prompt).text
            except: return "Server Busy. Please try again."
        return "Error: Connection failed."

# NEW: Audio Stream Function (No File Save)
async def generate_audio_base64(text):
    communicate = edge_tts.Communicate(text, VOICE)
    # Memory me audio store karega
    audio_stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    
    # Bytes ko Base64 string banakar return karega
    audio_base64 = base64.b64encode(audio_stream.getvalue()).decode('utf-8')
    return audio_base64

# --- Routes ---

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        try:
            # 1. File ko Gemini par upload karo
            sample_file = genai.upload_file(path=filepath, display_name=file.filename)
            
            # 2. IMPORTANT: Chat Session me file bhejo taaki memory me rahe
            # Hum user ki taraf se hidden message bhej rahe hain
            response = chat_session.send_message([sample_file, "Maine ye file upload ki hai. Isko padh lo aur yaad rakho. Ab iska summary do."])
            
            return jsonify({'success': True, 'message': response.text})
        except Exception as e:
            return jsonify({'success': False, 'message': f"Analysis failed: {str(e)}"})

@app.route('/execute_command', methods=['POST'])
def execute_command():
    data = request.json
    user_command = data.get('command', '').lower()
    is_voice = data.get('is_voice', False)

    # 1. Image Generation Check
    trigger_words = ["generate image", "create image", "draw", "photo of", "tasveer"]
    is_image = any(t in user_command for t in trigger_words) and not any(q in user_command for q in ["what is", "explain", "kya hai"])

    if is_image:
        # (Image logic same as before, skipped for brevity but keep your pollination code here if needed)
        # Assuming you have the generate_image_pollinations_and_save function
        return jsonify({'response': "Image feature temporarily disabled in code preview.", 'is_image': False})

    # 2. Normal Chat
    print(f"💬 Chat Request: {user_command}")
    response_text = get_gemini_response(user_command, is_voice)
    
    # 3. Audio Logic (Direct Streaming)
    audio_data = None
    has_audio = False
    
    if is_voice:
        try: 
            # Clean text remove markdown
            speech_text = remove_markdown(response_text)
            # Generate Base64 Audio
            audio_data = asyncio.run(generate_audio_base64(speech_text))
            has_audio = True
        except Exception as e:
            print(f"Audio Error: {e}")

    return jsonify({
        'response': response_text, 
        'is_image': False, 
        'has_audio': has_audio, 
        'audio_base64': audio_data # Direct audio string
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
