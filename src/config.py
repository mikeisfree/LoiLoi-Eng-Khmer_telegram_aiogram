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

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "km": {"name": "ខ្មែរ (Khmer)", "flag": "🇰🇭"},
    "pl": {"name": "Polski", "flag": "🇵🇱"},
}

# Available language pairs
LANGUAGE_PAIRS = [
    ("en", "km"),
    ("en", "pl"),
    ("km", "pl"),
]

# Default language pair
DEFAULT_LANG_PAIR = ("en", "km")

# UI Messages - English, Khmer and Polish
MESSAGES = {
    "en": {
        "welcome": """🎙️ Hi! I'm a multilingual voice translator bot.

📢 How to use:
• Send a voice message - I'll translate it automatically
• /t Hello - translate text
• /pair - choose language pair

🌐 Languages: 🇬🇧 English, 🇰🇭 ខ្មែរ, 🇵🇱 Polski

🔤 /lang - change interface language
ℹ️ /help - full command list""",

        "help": """📖 **Help - Multilingual Translator Bot**

**Commands:**
• `/start` - welcome message
• `/help` - this message
• `/t <text>` - translate text
• `/pair` - choose translation languages
• `/lang` - change interface language

**Voice messages:**
Send any voice message and the bot will:
1. Detect language
2. Transcribe the audio
3. Translate to the other language in your pair

⏱️ Max recording length: 60 seconds""",

        "lang_prompt": "🌐 Choose your interface language:",
        "lang_changed": "✅ Interface language changed to English",
        "pair_prompt": "🔄 Choose translation pair:",
        "pair_changed": "✅ Translation pair: {lang1} ↔ {lang2}",
        "current_pair": "Current pair: {lang1} ↔ {lang2}",
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
        "welcome": """🎙️ សួស្តី! ខ្ញុំជាបូតបកប្រែ។

📢 របៀបប្រើ:
• ផ្ញើសារជាសំឡេង
• /t Hello - បកប្រែអត្ថបទ
• /pair - ជ្រើសរើសភាសា

🌐 ភាសា: 🇬🇧 English, 🇰🇭 ខ្មែរ, 🇵🇱 Polski

🔤 /lang - ប្តូរភាសាចំណុចប្រទាក់
ℹ️ /help - ជំនួយ""",

        "help": """📖 **ជំនួយ - បូតបកប្រែ**

**ពាក្យបញ្ជា:**
• `/start` - សារស្វាគមន៍
• `/help` - សារនេះ
• `/t <អត្ថបទ>` - បកប្រែអត្ថបទ
• `/pair` - ជ្រើសរើសភាសាបកប្រែ
• `/lang` - ប្តូរភាសាចំណុចប្រទាក់

⏱️ រយៈពេលថតអតិបរមា: 60 វិនាទី""",

        "lang_prompt": "🌐 ជ្រើសរើសភាសាចំណុចប្រទាក់:",
        "lang_changed": "✅ ភាសាចំណុចប្រទាក់បានប្តូរទៅភាសាខ្មែរ",
        "pair_prompt": "🔄 ជ្រើសរើសភាសាបកប្រែ:",
        "pair_changed": "✅ ភាសាបកប្រែ: {lang1} ↔ {lang2}",
        "current_pair": "ភាសាបច្ចុប្បន្ន: {lang1} ↔ {lang2}",
        "error_audio_too_long": "⚠️ ការថតវែងពេក។ អតិបរមា: {max_seconds} វិនាទី។",
        "error_rate_limit": "⏳ លើសកំណត់។ សូមព្យាយាមម្តងទៀតក្នុង {minutes} នាទី។",
        "error_processing": "❌ មានបញ្ហាកើតឡើង។ សូមព្យាយាមម្តងទៀត។",
        "error_text_required": "⚠️ សូមបញ្ចូលអត្ថបទដើម្បីបកប្រែ។",
        "processing": "⏳ កំពុងដំណើរការ...",
        "detected_lang": "🎤 **ភាសារកឃើញ:** {lang}",
        "transcription": "📝 **ការសរសេរ:**",
        "translation": "🔄 **ការបកប្រែ:**",
    },
    "pl": {
        "welcome": """🎙️ Cześć! Jestem botem tłumaczącym głos.

📢 Jak używać:
• Wyślij wiadomość głosową
• /t Hello - tłumacz tekst
• /pair - wybierz parę języków

🌐 Języki: 🇬🇧 English, 🇰🇭 ខ្មែរ, 🇵🇱 Polski

🔤 /lang - zmień język interfejsu
ℹ️ /help - pomoc""",

        "help": """📖 **Pomoc - Bot Tłumaczący**

**Komendy:**
• `/start` - wiadomość powitalna
• `/help` - ta wiadomość
• `/t <tekst>` - tłumacz tekst
• `/pair` - wybierz języki tłumaczenia
• `/lang` - zmień język interfejsu

⏱️ Max długość nagrania: 60 sekund""",

        "lang_prompt": "🌐 Wybierz język interfejsu:",
        "lang_changed": "✅ Język interfejsu zmieniony na Polski",
        "pair_prompt": "🔄 Wybierz parę języków:",
        "pair_changed": "✅ Para języków: {lang1} ↔ {lang2}",
        "current_pair": "Obecna para: {lang1} ↔ {lang2}",
        "error_audio_too_long": "⚠️ Nagranie za długie. Maximum: {max_seconds} sekund.",
        "error_rate_limit": "⏳ Limit przekroczony. Spróbuj za {minutes} minut.",
        "error_processing": "❌ Wystąpił błąd. Spróbuj ponownie.",
        "error_text_required": "⚠️ Podaj tekst do tłumaczenia. Np: `/t Hello`",
        "processing": "⏳ Przetwarzanie...",
        "detected_lang": "🎤 **Wykryty język:** {lang}",
        "transcription": "📝 **Transkrypcja:**",
        "translation": "🔄 **Tłumaczenie:**",
    }
}

# Default language for new users
DEFAULT_LANG = "en"
