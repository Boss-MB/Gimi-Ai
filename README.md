# Gimi AI: Your Local Desktop AI Companion

Gimi AI is a conversational assistant designed to be a secure and personalized AI experience. This project demonstrates how to build a fully functional chatbot that operates directly from your local machine, not the cloud.

### Features

* **Local Backend:** The entire server-side logic runs on your computer using Python and Flask.
* **Web-based Frontend:** A clean and modern user interface built with HTML, CSS, and JavaScript.
* **Intelligent Responses:** Integrates with the Google Gemini API to provide smart and accurate answers.
* **Voice & Text Input:** Supports both typing and continuous voice commands for a seamless conversation.
* **Local PC Integration:** Capable of executing system commands like opening applications.
* **Formatted Output:** Renders AI responses with proper formatting (headings, paragraphs, etc.) for better readability.

### How It Works

Gimi AI's architecture is simple yet powerful:

1.  A user types or speaks a command into the web interface.
2.  The frontend (`script.js`) sends this command to the Python backend (`atlas.py`).
3.  The backend decides whether to execute a local PC command or send the query to the Gemini AI.
4.  The response is sent back to the frontend.
5.  The frontend displays the response in the chat box.

### Getting Started

**1. Clone the repository:**

```bash
git clone [https://github.com/your-username/atlas-ai.git](https://github.com/your-username/atlas-ai.git)
```
**2.Install dependencies:**

```bash
pip install -r requirements.txt
```

**3.Set up your Gemini API Key:**
Create a file named .env in the project root directory and add your API key:
```bash
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```
**Note**: Replace YOUR_API_KEY_HERE with your actual key from the Google AI Studio.

**4. Run the application:**
Use the included batch file to start the server and open the web app.

```bash
start_chatbot.bat
```

**Project Structure**

```bash
Gimi Ai/
├── .env
├── Gimi.py
├── start_chatbot.bat
├── requirements.txt
├── Frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
```
