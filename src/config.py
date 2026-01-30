"""
Configuration module - loads environment variables and defines constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Limits (MVP - test values)
MAX_AUDIO_DURATION_SECONDS = int(os.getenv("MAX_AUDIO_DURATION_SECONDS", 60))
MAX_REQUESTS_PER_USER_PER_HOUR = int(os.getenv("MAX_REQUESTS_PER_USER_PER_HOUR", 30))
TEMP_CLEANUP_AFTER_FILES = int(os.getenv("TEMP_CLEANUP_AFTER_FILES", 10))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Paths
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

# Supported languages (prepared for v2 expansion)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "km": "Khmer",
    # v2:
    # "pl": "Polish",
}

# UI Messages - English and Khmer
MESSAGES = {
    "en": {
        "welcome": """🎙️ Hi! I'm an English ↔️ Khmer translator bot.

📢 How to use:
• Send a voice message - I'll translate it automatically
• OR
• /t Hello, how are you? - translate text

🌐 Supported languages: English, ភាសាខ្មែរ (Khmer)

🔤 /lang - change interface language
ℹ️ /help - full command list""",

        "help": """📖 **Help - EN↔KM Translator Bot**

**Commands:**
• `/start` - welcome message
• `/help` - this message
• `/t <text>` - translate text
• `/lang` - change interface language

**Examples:**
• `/t Hello, how are you?` → សួស្តី តើអ្នកសុខសប្បាយទេ?
• `/t សួស្តី` → Hello

**Voice messages:**
Send any voice message and the bot will:
1. Detect language (EN or KM)
2. Transcribe the audio
3. Translate to the other language

⏱️ Max recording length: 60 seconds""",

        "lang_prompt": "🌐 Choose your interface language:",
        "lang_changed": "✅ Interface language changed to English",
        "error_audio_too_long": "⚠️ Recording too long. Maximum: {max_seconds} seconds.",
        "error_rate_limit": "⏳ Rate limit exceeded. Try again in {minutes} minutes.",
        "error_processing": "❌ An error occurred. Please try again.",
        "error_text_required": "⚠️ Please provide text to translate. Example: `/t Hello`",
        "processing": "⏳ Processing...",
        "detected_lang": "🎤 **Detected language:** {lang}",
        "transcription": "📝 **Transcription:**",
        "translation": "🔄 **Translation:**",
    },
    "km": {
        "welcome": """🎙️ សួស្តី! ខ្ញុំជាបូតបកប្រែ អង់គ្លេស ↔️ ខ្មែរ។

📢 របៀបប្រើ:
• ផ្ញើសារជាសំឡេង - ខ្ញុំនឹងបកប្រែដោយស្វ័យប្រវត្តិ
• /t Hello, how are you? - បកប្រែអត្ថបទ

🌐 ភាសាដែលគាំទ្រ: English, ភាសាខ្មែរ

🔤 /lang - ប្តូរភាសាចំណុចប្រទាក់
ℹ️ /help - បញ្ជីពាក្យបញ្ជាពេញ""",

        "help": """📖 **ជំនួយ - បូតបកប្រែ EN↔KM**

**ពាក្យបញ្ជា:**
• `/start` - សារស្វាគមន៍
• `/help` - សារនេះ
• `/t <អត្ថបទ>` - បកប្រែអត្ថបទ
• `/lang` - ប្តូរភាសាចំណុចប្រទាក់

**ឧទាហរណ៍:**
• `/t Hello, how are you?` → សួស្តី តើអ្នកសុខសប្បាយទេ?
• `/t សួស្តី` → Hello

**សារជាសំឡេង:**
ផ្ញើសារជាសំឡេងណាមួយ ហើយបូតនឹង:
1. រកភាសា (EN ឬ KM)
2. សរសេរសំឡេង
3. បកប្រែទៅភាសាផ្សេង

⏱️ រយៈពេលថតអតិបរមា: 60 វិនាទី""",

        "lang_prompt": "🌐 ជ្រើសរើសភាសាចំណុចប្រទាក់របស់អ្នក:",
        "lang_changed": "✅ ភាសាចំណុចប្រទាក់បានប្តូរទៅភាសាខ្មែរ",
        "error_audio_too_long": "⚠️ ការថតវែងពេក។ អតិបរមា: {max_seconds} វិនាទី។",
        "error_rate_limit": "⏳ លើសកំណត់។ សូមព្យាយាមម្តងទៀតក្នុង {minutes} នាទី។",
        "error_processing": "❌ មានបញ្ហាកើតឡើង។ សូមព្យាយាមម្តងទៀត។",
        "error_text_required": "⚠️ សូមបញ្ចូលអត្ថបទដើម្បីបកប្រែ។ ឧទាហរណ៍: `/t Hello`",
        "processing": "⏳ កំពុងដំណើរការ...",
        "detected_lang": "🎤 **ភាសាដែលបានរកឃើញ:** {lang}",
        "transcription": "📝 **ការសរសេរ:**",
        "translation": "🔄 **ការបកប្រែ:**",
    }
}

# Default language for new users
DEFAULT_LANG = "en"
