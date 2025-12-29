import os
import asyncio
import edge_tts
import re
import requests 
import random
import time
import base64 
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables (Local testing ke liye, Render pe Dashboard me dalenge)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__, template_folder='Frontend', static_folder='Frontend')
CORS(app)

# Folders setup
IMAGE_FOLDER = os.path.join('Frontend', 'generated_images')
os.makedirs(IMAGE_FOLDER, exist_ok=True) 
UPLOAD_FOLDER = os.path.join('Frontend', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API Keys Setup
gemini_keys = [os.getenv("GEMINI_API_KEY_1"), os.getenv("GEMINI_API_KEY_2")]
current_gemini_index = 0
VOICE = "en-IN-PrabhatNeural"
AUDIO_FILE_PATH = os.path.join("Frontend", "response.mp3")

# Configure Gemini
def configure_genai():
    global current_gemini_index
    if current_gemini_index < len(gemini_keys) and gemini_keys[current_gemini_index]:
        genai.configure(api_key=gemini_keys[current_gemini_index])
    else:
        print("❌ No valid Gemini keys found.")
configure_genai()

# Models
model = genai.GenerativeModel('models/gemini-2.5-flash-lite', system_instruction="You are Gimi AI. Answer helpful and concisely. Use HINGLISH for Hindi responses.")
chat_session = model.start_chat(history=[])
prompt_model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

# --- Helper Functions ---

def enhance_image_prompt(user_prompt):
    try:
        response = prompt_model.generate_content(f"Rewrite into detailed photorealistic prompt: '{user_prompt}'")
        return response.text.strip()
    except: return user_prompt

def generate_image_pollinations_and_save(prompt):
    try:
        detailed_prompt = enhance_image_prompt(prompt)
        seed = random.randint(1, 100000)
        encoded_prompt = requests.utils.quote(detailed_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&nologo=true&model=flux" 
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(image_url, headers=headers, timeout=60) 
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', '').lower():
            image_data = response.content
            return base64.b64encode(image_data).decode('utf-8')
        return None
    except: return None

def remove_markdown(text): 
    return re.sub(' +', ' ', text.replace('*', '').replace('#', '').replace('_', '')).strip()

def get_gemini_response(prompt, is_voice=False):
    global current_gemini_index, chat_session, model
    try:
        return chat_session.send_message(prompt).text
    except:
        # Retry Logic
        if current_gemini_index < len(gemini_keys) - 1:
            current_gemini_index += 1
            configure_genai()
            chat_session = model.start_chat(history=chat_session.history)
            try: return chat_session.send_message(prompt).text
            except: return "Error: Connection failed."
        return "Error: Connection failed."

async def generate_audio(text):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(AUDIO_FILE_PATH)

# --- Routes ---

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/get_audio')
def get_audio():
    try: return send_file(AUDIO_FILE_PATH, mimetype="audio/mp3")
    except: return "Error", 404

# File Upload Route (Fix for JS error)
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
        
        # Process file with Gemini (Simple analysis)
        try:
            sample_file = genai.upload_file(path=filepath, display_name=file.filename)
            response = model.generate_content([sample_file, "Analyze this document and summarize it."])
            return jsonify({'success': True, 'message': response.text})
        except Exception as e:
            return jsonify({'success': True, 'message': f"File uploaded. Analysis failed: {str(e)}"})

@app.route('/execute_command', methods=['POST'])
def execute_command():
    data = request.json
    user_command = data.get('command', '').lower()
    is_voice = data.get('is_voice', False)

    # 1. Image Generation Check
    trigger_words = ["generate image", "create image", "draw", "photo of", "picture of", "tasveer"]
    is_image = any(t in user_command for t in trigger_words) and not any(q in user_command for q in ["what is", "explain", "kya hai"])

    if is_image:
        print(f"🎨 Image Request: {user_command}")
        img_base64 = generate_image_pollinations_and_save(user_command)
        if img_base64:
            try: asyncio.run(generate_audio("Here is the image.")) 
            except: pass
            return jsonify({'response': "", 'is_image': True, 'image_data': img_base64, 'has_audio': True, 'audio_url': '/get_audio'})
        else:
             return jsonify({'response': "Sorry, image generation failed.", 'is_image': False, 'has_audio': False})

    # 2. Normal Chat
    print(f"💬 Chat Request: {user_command}")
    response_text = get_gemini_response(user_command, is_voice)
    
    # Clean text for speech
    speech_text = remove_markdown(response_text.split("|||")[1] if "|||" in response_text else response_text)
    
    has_audio = False
    if is_voice:
        try: 
            asyncio.run(generate_audio(speech_text))
            has_audio = True
        except: pass

    return jsonify({'response': response_text.split("|||")[0], 'is_image': False, 'has_audio': has_audio, 'audio_url': '/get_audio'})

if __name__ == '__main__':
    # '0.0.0.0' is important for Render
    app.run(host='0.0.0.0', port=5000)

