# LoiLoi: Multilingual Voice Translator

Bidirectional voice translator for **English (EN) ↔️ Khmer (KM) ↔️ Polish (PL)** available as:

- 🤖 **Telegram Bot** (Python/aiogram)
- 📱 **Android App** (Capacitor)

---

## Features

- 🎤 Voice recording with automatic language detection
- 📝 Speech-to-text transcription
- 🔄 Instant translation between any language pair.
- ⚙️ User-configurable Gemini API key

---

## 📱 Android App

### Features

- Flag-based language pair selector (eg. 🇬🇧 🇰🇭 🇵🇱)
- Select any 2 languages for translation
- Animated synthwave background with moving grid
- Microphone permission requested on app launch

### Tech Stack

- **Frontend:** HTML/CSS/JavaScript
- **Build:** Capacitor (native Android wrapper)
- **AI:** Google Gemini 2.0 Flash

### Quick Start

1. Copy APK from `android/app/build/outputs/apk/debug/app-debug.apk`
2. Install on Android device
3. Set your Gemini API key in Settings
4. Select 2 languages and start translating!

### Build APK

```bash
cd app
npm install
npx cap sync
cd android
JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew assembleDebug
```

### Local Development

```bash
cd app
npx http-server www -p 3000 -c-1
```

---

## 🤖 Telegram Bot

### Features

- `/pair` — select translation language pair
- `/lang` — change UI language (EN/KM/PL)
- Voice messages auto-transcribed and translated
- Text translation with `/t <text>`

### Bot Commands

| Command         | Description                  |
| --------------- | ---------------------------- |
| `/start`        | Welcome message              |
| `/help`         | Help and examples            |
| `/pair`         | Choose translation languages |
| `/lang`         | Choose interface language    |
| `/t <text>`     | Translate text               |
| _voice message_ | Transcribe + translate audio |

### Configuration (.env)

```ini
TELEGRAM_BOT_TOKEN=your_token
GOOGLE_API_KEY=your_gemini_key
MAX_AUDIO_DURATION_SECONDS=60
MAX_REQUESTS_PER_USER_PER_HOUR=30
```

### Docker Deployment

```bash
docker compose up -d --build
```

---

## Project Structure

```text
.
├── app/                    # Mobile app
│   ├── www/                # Web assets
│   └── android/            # Android project
├── src/                    # Telegram bot
│   ├── main.py
│   ├── config.py
│   ├── handlers.py
│   └── services/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Roadmap

- [x] Polish language support
- [x] Language pair selection
- [ ] TTS (Text-to-Speech) audio response
- [ ] Thai language
- [ ] iOS app version
