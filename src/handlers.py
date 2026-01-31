"""
Handlers - Telegram message and command handlers.
Uses Gemini for both STT and translation (single API call).
"""
import os
import logging
import asyncio
from collections import defaultdict

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatAction

from config import (
    TEMP_DIR,
    MESSAGES,
    DEFAULT_LANG,
    MAX_AUDIO_DURATION_SECONDS,
)
from services.rate_limiter import rate_limiter
from services.audio_service import (
    ensure_temp_dir,
    compress_audio,
    check_audio_duration,
    cleanup_temp_files,
    delete_files,
)
from services.ai_service import translate_audio, translate_text

logger = logging.getLogger(__name__)

# Create router
router = Router()

# User language preferences (in-memory storage)
user_languages: dict[int, str] = defaultdict(lambda: DEFAULT_LANG)


def get_msg(user_id: int, key: str) -> str:
    """Get message in user's preferred language."""
    lang = user_languages[user_id]
    return MESSAGES.get(lang, MESSAGES[DEFAULT_LANG]).get(key, "")


def get_lang_name(lang_code: str) -> str:
    """Get language display name."""
    return "English" if lang_code == "en" else "ខ្មែរ (Khmer)" if lang_code == "km" else lang_code


def format_voice_response(user_id: int, result: dict) -> str:
    """Format voice message response."""
    lang = result.get("lang", "?")
    lang_name = get_lang_name(lang)
    
    msg = get_msg(user_id, "detected_lang").format(lang=lang_name)
    msg += f"\n\n{get_msg(user_id, 'transcription')}\n{result.get('text', '—')}"
    msg += f"\n\n{get_msg(user_id, 'translation')}\n{result.get('translation', '—')}"
    
    return msg


def format_text_response(user_id: int, original: str, result: dict) -> str:
    """Format text translation response."""
    source = get_lang_name(result.get("from", "en"))
    target = get_lang_name(result.get("to", "km"))
    
    msg = f"📝 **{source} → {target}**\n\n{original}"
    msg += f"\n\n{get_msg(user_id, 'translation')}\n{result.get('translation', '—')}"
    
    return msg


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Create language selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇰🇭 ខ្មែរ", callback_data="lang_km"),
        ]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    await message.answer(get_msg(user_id, "welcome"))


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    user_id = message.from_user.id
    await message.answer(get_msg(user_id, "help"), parse_mode="Markdown")


@router.message(Command("lang"))
async def cmd_lang(message: Message):
    """Handle /lang command - show language selection."""
    user_id = message.from_user.id
    await message.answer(
        get_msg(user_id, "lang_prompt"),
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def callback_lang(callback: CallbackQuery):
    """Handle language selection callback."""
    user_id = callback.from_user.id
    lang_code = callback.data.replace("lang_", "")
    
    if lang_code in MESSAGES:
        user_languages[user_id] = lang_code
        await callback.message.edit_text(MESSAGES[lang_code]["lang_changed"])
    
    await callback.answer()


@router.message(Command("t"))
async def cmd_translate_text(message: Message):
    """Handle /t <text> command for text translation."""
    user_id = message.from_user.id
    
    # Check rate limit
    allowed, minutes = rate_limiter.check(user_id)
    if not allowed:
        await message.answer(
            get_msg(user_id, "error_rate_limit").format(minutes=minutes)
        )
        return
    
    # Extract text after /t
    text = message.text
    if text:
        parts = text.split(maxsplit=1)
        text = parts[1] if len(parts) > 1 else ""
    
    if not text or not text.strip():
        await message.answer(get_msg(user_id, "error_text_required"))
        return
    
    rate_limiter.record(user_id)
    
    # Typing indicator
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    try:
        result = await translate_text(text.strip())
        response = format_text_response(user_id, text.strip(), result)
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        await message.answer(get_msg(user_id, "error_processing"))


@router.message(F.voice)
async def handle_voice(message: Message):
    """
    Handle voice messages:
    1. Download audio
    2. Compress (8kHz OGG)
    3. Gemini: STT + translate (single API call)
    """
    user_id = message.from_user.id
    
    # Check rate limit
    allowed, minutes = rate_limiter.check(user_id)
    if not allowed:
        await message.answer(
            get_msg(user_id, "error_rate_limit").format(minutes=minutes)
        )
        return
    
    ensure_temp_dir()
    
    voice = message.voice
    file_id = voice.file_id
    oga_path = os.path.join(TEMP_DIR, f"{file_id}.oga")
    compressed_path = None
    
    try:
        # Send processing message
        processing_msg = await message.answer(get_msg(user_id, "processing"))
        
        # Download file
        file = await message.bot.get_file(file_id)
        await message.bot.download_file(file.file_path, oga_path)
        
        # Check duration
        is_valid, duration = check_audio_duration(oga_path)
        if not is_valid:
            await processing_msg.delete()
            await message.answer(
                get_msg(user_id, "error_audio_too_long").format(
                    max_seconds=MAX_AUDIO_DURATION_SECONDS
                )
            )
            delete_files(oga_path)
            return
        
        rate_limiter.record(user_id)
        
        # Compress audio (8kHz mono OGG) - faster upload
        compressed_path = compress_audio(oga_path)
        
        # Gemini: STT + translate in single call
        result = await translate_audio(compressed_path)
        
        # Send result
        await processing_msg.delete()
        response = format_voice_response(user_id, result)
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await message.answer(get_msg(user_id, "error_processing"))
    finally:
        # Cleanup in background
        delete_files(oga_path, compressed_path)
        cleanup_temp_files()
