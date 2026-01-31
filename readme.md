# LoiLoi: English ↔️ Khmer Voice Translator

Bidirectional voice translator for **English (EN) ↔️ Khmer (KM) ↔️ Polish (PL)** available as:

- 🤖 **Telegram Bot** (Python/aiogram)
- 📱 **Android App** (Capacitor)

---

## Features

- 🎤 Voice recording with automatic language detection
- 📝 Speech-to-text transcription
- 🔄 Instant translation (EN↔KM)
- ⚙️ User-configurable Gemini API key (mobile app)
- 🌐 Bilingual UI (English/Khmer)

---

## 📱 Android App

### Tech Stack

- **Frontend:** HTML/CSS/JavaScript
- **Build:** Capacitor (native Android wrapper)
- **AI:** Google Gemini 2.0 Flash (direct API calls)

### Project Structure

```text
app/
├── www/                    # Web assets (used by Capacitor)
│   ├── index.html          # Main UI
│   ├── styles.css          # Dark theme styles
│   └── app.js              # Audio recording + Gemini API
├── android/                # Android project (generated)
├── capacitor.config.json   # Capacitor configuration
└── package.json
```

### Use build APK file

- Copy APK file from `android/app/build/outputs/apk/debug/loiloi.apk` to your Android device.

- Install from there

- Done

### Other options

### Build APK

```bash
# Prerequisites: Node.js, Java 21, Android SDK

cd app

# Install dependencies
npm install

# Sync web assets to Android
npx cap sync

# Build APK (requires Android SDK)
cd android
JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew assembleDebug

# APK location:
# android/app/build/outputs/apk/debug/app-debug.apk
```

### Local Development

```bash
cd app
npx http-server www -p 3000 -c-1
# Open http://localhost:3000
```

---

## 🤖 Telegram Bot

### Tech Stack

- **Language:** Python 3.10+
- **Framework:** aiogram 3.x
- **AI:** Google Gemini 2.0 Flash
- **Audio:** FFmpeg + pydub

### Bot Commands

| Command         | Description                             |
| --------------- | --------------------------------------- |
| `/start`        | Welcome message with usage instructions |
| `/help`         | Help - command list and examples        |
| `/t <text>`     | Text translation (auto-detect EN↔KM)    |
| _voice message_ | Audio transcription + translation       |

### Project Structure

```text
src/
├── main.py             # Entry point
├── config.py           # Configuration
├── handlers.py         # Message handlers
└── services/
    ├── audio_service.py    # Audio processing
    ├── ai_service.py       # Gemini API
    └── rate_limiter.py     # Rate limiting
```

### Configuration (.env)

```ini
TELEGRAM_BOT_TOKEN=your_token_from_botfather
GOOGLE_API_KEY=your_google_ai_studio_key
MAX_AUDIO_DURATION_SECONDS=60
MAX_REQUESTS_PER_USER_PER_HOUR=30
```

### Docker Deployment

```bash
docker compose up -d
```

---

## Roadmap

- [ ] TTS (Text-to-Speech) audio response
- [ ] Additional language pairs (Polish, Thai)
- [ ] iOS app version
- [ ] Offline mode with local models
