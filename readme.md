# Telegram "LoiLoi" Bot: English ↔️ Khmer Voice Translator (MVP + Roadmap)

## 1. Project Overview

Telegram bot that serves as a bidirectional voice translator for the language pair **English (EN) ↔️ Khmer (KM)**.

### MVP (Minimum Viable Product)

Bot:

1. Receives a voice message.
2. Automatically detects the speaker's language.
3. Performs transcription (Speech-to-Text).
4. Translates the text to the other language.
5. Sends back a text response containing transcription and translation.

### Additional MVP Features:

- **Command `/t <text>`** – text translation (without audio)
- **Command `/start`** – welcome message with instructions
- **Command `/help`** – help

### v2 (Roadmap)

- Text-to-Speech synthesis – audio response
- Ability to extend with additional language pairs (e.g., Polish ↔️ Khmer)

---

## 2. Tech Stack

### Backend & Framework

- **Language:** Python 3.10+
- **Telegram API Framework:** `aiogram` (version 3.x)
- **Environment Variables Management:** `python-dotenv`

### AI & Processing (MVP)

- **Main Model:** **Google Gemini 1.5 Flash**
  - _Role:_ STT (transcription) + language detector + translator
  - _Why:_ Fast, cheap, good support for Asian languages
- **SDK:** `google-generativeai`

### Audio Processing

- **System:** `FFmpeg` (in Docker container)
- **Python Wrapper:** `pydub` – conversion `.oga` → `.mp3`

### Deployment

- **Containerization:** Docker + Docker Compose
- **Target Hosting:** Coolify + VPS

---

## 3. Project Structure

```text
telegram-translator-bot/
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Container image
├── .env                    # API keys (do not commit!)
├── .env.example            # Example .env file
├── .gitignore
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py             # Entry point, bot initialization
│   ├── config.py           # Loading variables + configuration constants
│   ├── handlers.py         # Message handling logic (aiogram Routers)
│   └── services/
│       ├── __init__.py
│       ├── audio_service.py    # OGG -> MP3 conversion + temp cleanup
│       ├── ai_service.py       # Gemini API communication
│       └── rate_limiter.py     # Simple per-user rate limiter
└── temp/                   # Temporary audio files folder
```

---

## 4. Configuration (.env)

```ini
# Telegram
TELEGRAM_BOT_TOKEN=your_token_from_botfather

# Google AI
GOOGLE_API_KEY=your_google_ai_studio_key

# Limits (MVP - test values)
MAX_AUDIO_DURATION_SECONDS=60
MAX_REQUESTS_PER_USER_PER_HOUR=30
TEMP_CLEANUP_AFTER_FILES=10

# Logs
LOG_LEVEL=INFO
```

### requirements.txt

```text
aiogram>=3.0.0
google-generativeai
pydub
python-dotenv
aiofiles
```

---

## 5. Bot Commands

| Command         | Description                             |
| --------------- | --------------------------------------- |
| `/start`        | Welcome message with usage instructions |
| `/help`         | Help - command list and examples        |
| `/t <text>`     | Text translation (auto-detect EN↔KM)    |
| _voice message_ | Audio transcription + translation       |

### Example `/start`:

```
🎙️ Hi! I'm an English ↔️ Khmer translator bot.

📢 How to use:
• Send a voice message - I'll translate it automatically
• /t Hello, how are you? - translate text

🌐 Supported languages: English, ភាសាខ្មែរ (Khmer)
```

---

## 6. Limits and Security (MVP)

### Audio Limits

- **Max recording length:** 60 seconds
- On exceed: "⚠️ Recording too long. Max: 60 seconds."

### Rate Limiting (per user)

- **Max requests/hour:** 30
- On exceed: "⏳ Rate limit exceeded. Try again in X minutes."

### Temporary File Cleanup

- Automatic cleanup of `temp/` folder every **10 processed files**
- Files older than 5 minutes are deleted

---

## 7. Core Logic (AI Service)

### System Prompt for Gemini

```python
# ai_service.py

VOICE_PROMPT = """
You are a simultaneous interpreter for English and Khmer (Cambodian).
Task:
1. Listen to the attached audio file.
2. Detect the language: is it English ('en') or Khmer ('km')?
3. Transcribe the audio exactly as spoken.
4. Translate it to the target language (EN -> KM or KM -> EN).

Output format: Return ONLY a raw JSON object (no markdown, no code blocks).
{
    "detected_lang": "en",
    "transcription": "Original text...",
    "translation": "Translated text..."
}
"""

TEXT_PROMPT = """
You are a translator for English and Khmer (Cambodian).
Task:
1. Detect if the input text is English ('en') or Khmer ('km').
2. Translate it to the other language.

Output format: Return ONLY a raw JSON object.
{
    "detected_lang": "en",
    "original": "Input text...",
    "translation": "Translated text..."
}
"""
```

### JSON Parsing (with error handling)

````python
import json
import re

def parse_gemini_response(response_text: str) -> dict:
    """Parse Gemini response, remove markdown if present."""
    # Remove markdown code blocks if they exist
    cleaned = re.sub(r'^```json\s*', '', response_text.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("Failed to process AI response")
````

---

## 8. Docker Compose (Deployment)

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
RUN mkdir -p /app/temp

CMD ["python", "src/main.py"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  bot:
    build: .
    container_name: engkh-translator-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./temp:/app/temp
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Deployment on Coolify

1. Push repo to GitHub/GitLab
2. In Coolify: New Resource → Docker Compose
3. Connect repo and set environment variables
4. Deploy

---

## 9. Development Roadmap: Version v2

### TTS (Text-to-Speech)

- **Recommendation:** Microsoft Azure AI Speech (`km-KH-PisethNeural`)
- **Alternative:** Google Cloud TTS

### Additional Language Pairs (v2+)

Architecture allows easy extension:

```python
# config.py
SUPPORTED_LANGUAGES = {
    "en": "English",
    "km": "Khmer",
    # v2:
    # "pl": "Polish",
}
```

---

## 10. MVP Checklist

- [x] Project structure
- [x] Dockerfile + docker-compose.yml
- [x] `config.py` - environment variables + constants
- [x] `handlers.py` - /start, /help, /t, voice handler
- [x] `ai_service.py` - Gemini communication
- [x] `audio_service.py` - conversion + temp cleanup
- [x] `rate_limiter.py` - simple per-user limiter
- [ ] Local testing
- [ ] Deploy to Coolify
