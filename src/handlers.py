"""
Handlers - Telegram message and command handlers.
Uses Gemini for both STT and translation.
Automatically translates between Polish and Ukrainian with context.
"""
import os
import re
import html
import logging
import asyncio
from collections import defaultdict, deque

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.enums import ChatAction

from config import (
    TEMP_DIR,
    MESSAGES,
    DEFAULT_LANG,
    DEFAULT_LANG_PAIR,
    SUPPORTED_LANGUAGES,
    LANGUAGE_PAIRS,
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
from services.ai_service import translate_audio, translate_text, translate_text_with_context

logger = logging.getLogger(__name__)

# Create router
router = Router()

# User preferences (in-memory storage)
user_languages: dict[int, str] = defaultdict(lambda: DEFAULT_LANG)
user_lang_pairs: dict[int, tuple] = defaultdict(lambda: DEFAULT_LANG_PAIR)

# Conversation context storage (per chat, not per user)
# Stores last N messages as list of strings for context
# Format: ["role: content", ...] where role is 'user' or 'assistant'
chat_contexts: dict[int, deque] = defaultdict(deque)
CONTEXT_SIZE = 5  # Number of previous message pairs to keep for context

# Raw chat history (per chat) - every text message seen, used as translation context
# Format: ["Author: text", ...]
HISTORY_SIZE = 10  # Number of previous chat messages sent to the model as context
chat_history: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_SIZE))

# Track which chats have received the welcome message
welcomed_chats: set = set()

CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def get_msg(user_id: int, key: str) -> str:
    """Get message in user's preferred language."""
    lang = user_languages[user_id]
    return MESSAGES.get(lang, MESSAGES[DEFAULT_LANG]).get(key, "")


def get_lang_name(lang_code: str) -> str:
    """Get language display name."""
    lang_info = SUPPORTED_LANGUAGES.get(lang_code)
    if lang_info:
        return f"{lang_info['flag']} {lang_info['name']}"
    return lang_code


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
    """Create language selection keyboard (for UI language)."""
    buttons = []
    for code, info in SUPPORTED_LANGUAGES.items():
        buttons.append(InlineKeyboardButton(
            text=f"{info['flag']} {info['name']}", 
            callback_data=f"lang_{code}"
        ))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def get_pair_keyboard() -> InlineKeyboardMarkup:
    """Create language pair selection keyboard."""
    buttons = []
    for lang1, lang2 in LANGUAGE_PAIRS:
        info1 = SUPPORTED_LANGUAGES[lang1]
        info2 = SUPPORTED_LANGUAGES[lang2]
        buttons.append([InlineKeyboardButton(
            text=f"{info1['flag']} {info1['name']} ↔ {info2['flag']} {info2['name']}", 
            callback_data=f"pair_{lang1}_{lang2}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def add_context(chat_id: int, role: str, content: str) -> None:
    """Add a message to the chat context."""
    context = chat_contexts[chat_id]
    context.append(f"{role}: {content}")
    # Keep only last CONTEXT_SIZE message pairs (2 messages = 1 pair)
    while len(context) > CONTEXT_SIZE * 2:
        context.popleft()


def get_context(chat_id: int) -> list:
    """Get the current context for a chat."""
    return list(chat_contexts.get(chat_id, deque()))


def clear_context(chat_id: int) -> None:
    """Clear the context for a chat."""
    if chat_id in chat_contexts:
        chat_contexts[chat_id].clear()


def add_history(chat_id: int, author: str, text: str) -> None:
    """Remember a chat message so later translations get context."""
    chat_history[chat_id].append(f"{author}: {text}")


def get_history(chat_id: int) -> list:
    """Get previous chat messages for context."""
    return list(chat_history.get(chat_id, deque()))


def get_author(message: Message) -> str:
    """Display name of the message author (works for groups and channels)."""
    if message.from_user:
        return message.from_user.full_name
    return message.author_signature or message.chat.title or "?"


def detect_language(text: str) -> str:
    """
    Simple language detection for Polish and Ukrainian.
    Uses common characters and patterns.
    """
    text_lower = text.lower()

    # Polish uses Latin script only - any Cyrillic means Ukrainian
    if CYRILLIC_RE.search(text_lower):
        return "uk"
    
    # Ukrainian specific characters (Cyrillic)
    ukrainian_cyrillic = ['є', 'і', 'ї', 'ґ']
    # Polish specific characters (with diacritics)
    polish_diacritics = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
    
    # Count Ukrainian Cyrillic characters
    ukrainian_count = sum(1 for char in ukrainian_cyrillic if char in text_lower)
    
    # Count Polish diacritic characters
    polish_count = sum(1 for char in polish_diacritics if char in text_lower)
    
    # If we found Cyrillic characters, it's likely Ukrainian
    if ukrainian_count > 0:
        return "uk"
    
    # If we found Polish diacritics, it's likely Polish
    if polish_count > 0:
        return "pl"
    
    # Fallback: check for common words
    ukrainian_words = ['я', 'ти', 'він', 'вона', 'ми', 'ви', 'вони', 'це', 'сь', 'ться', 'шcho']
    polish_words = ['ja', 'ty', 'on', 'ona', 'my', 'wy', 'oni', 'się', 'cie', 'to', 'jest']
    
    ukrainian_word_count = sum(1 for word in ukrainian_words if f' {word} ' in f' {text_lower} ' or text_lower.startswith(word + ' ') or text_lower.endswith(' ' + word))
    polish_word_count = sum(1 for word in polish_words if f' {word} ' in f' {text_lower} ' or text_lower.startswith(word + ' ') or text_lower.endswith(' ' + word))
    
    if ukrainian_word_count > polish_word_count:
        return "uk"
    
    # Default to Polish if we can't determine
    return "pl"


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Clear context on start for fresh conversation
    clear_context(chat_id)
    chat_history.pop(chat_id, None)
    
    # Send welcome message if not already sent
    if chat_id not in welcomed_chats:
        welcomed_chats.add(chat_id)
        await message.answer(get_msg(user_id, "welcome"))


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    user_id = message.from_user.id
    await message.answer(get_msg(user_id, "help"), parse_mode="Markdown")


@router.message(Command("clear"))
async def cmd_clear_context(message: Message):
    """Handle /clear command - clear conversation context."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    clear_context(chat_id)
    chat_history.pop(chat_id, None)
    await message.answer(get_msg(user_id, "context_cleared"))


@router.message(Command("lang"))
async def cmd_lang(message: Message):
    """Handle /lang command - show UI language selection."""
    user_id = message.from_user.id
    await message.answer(
        get_msg(user_id, "lang_prompt"),
        reply_markup=get_language_keyboard()
    )


@router.message(Command("pair"))
async def cmd_pair(message: Message):
    """Handle /pair command - show language pair selection."""
    user_id = message.from_user.id
    pair = user_lang_pairs[user_id]
    lang1_name = get_lang_name(pair[0])
    lang2_name = get_lang_name(pair[1])
    
    current = get_msg(user_id, "current_pair").format(lang1=lang1_name, lang2=lang2_name)
    prompt = get_msg(user_id, "pair_prompt")
    
    await message.answer(
        f"{current}\n\n{prompt}",
        reply_markup=get_pair_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def callback_lang(callback: CallbackQuery):
    """Handle UI language selection callback."""
    user_id = callback.from_user.id
    lang_code = callback.data.replace("lang_", "")
    
    if lang_code in MESSAGES:
        user_languages[user_id] = lang_code
        await callback.message.edit_text(MESSAGES[lang_code]["lang_changed"])
    
    await callback.answer()


@router.callback_query(F.data.startswith("pair_"))
async def callback_pair(callback: CallbackQuery):
    """Handle language pair selection callback."""
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    
    if len(parts) == 3:
        lang1, lang2 = parts[1], parts[2]
        user_lang_pairs[user_id] = (lang1, lang2)
        
        lang1_name = get_lang_name(lang1)
        lang2_name = get_lang_name(lang2)
        
        msg = get_msg(user_id, "pair_changed").format(lang1=lang1_name, lang2=lang2_name)
        await callback.message.edit_text(msg)
    
    await callback.answer()


@router.message(Command("t"))
async def cmd_translate_text(message: Message):
    """Handle /t <text> command for explicit text translation."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
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
    await message.bot.send_chat_action(chat_id, ChatAction.TYPING)
    
    try:
        # Get user's language pair
        lang_pair = user_lang_pairs[user_id]
        
        # Detect language
        detected_lang = detect_language(text.strip())
        
        # Get context
        context = get_context(chat_id)
        
        # Translate with context
        result = await translate_text_with_context(
            text.strip(),
            lang_pair,
            context,
            detected_lang
        )
        
        # Add to context
        add_context(chat_id, "user", text.strip())
        add_context(chat_id, "assistant", result.get('translation', ''))
        
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
    3. Gemini: STT + translate
    4. Add to conversation context
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
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
        
        # Use the default pair (pl, uk) for auto-translation
        lang_pair = ("pl", "uk")
        
        # Get context
        context = get_context(chat_id)
        
        # Gemini: STT + translate with context
        result = await translate_audio(compressed_path, lang_pair)
        
        # Add to context
        add_context(chat_id, "user", result.get('text', ''))
        add_context(chat_id, "assistant", result.get('translation', ''))
        
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


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_bot_added(event: ChatMemberUpdated):
    """Bot was added to a group/channel - greet immediately, no /start needed."""
    chat_id = event.chat.id
    logger.info(f"Added to chat {chat_id} ({event.chat.type}: {event.chat.title})")
    if chat_id in welcomed_chats:
        return
    welcomed_chats.add(chat_id)
    welcome = f"{MESSAGES['pl']['welcome']}\n\n{MESSAGES['uk']['welcome']}"
    try:
        await event.bot.send_message(chat_id, welcome)
    except Exception as e:
        # e.g. channel where the bot is not an admin yet
        logger.warning(f"Cannot send welcome to {chat_id}: {e}")


@router.message(F.text)
async def handle_text_message(message: Message):
    """Group / private chat text - auto-translate PL <-> UK."""
    await auto_translate(message)


@router.channel_post(F.text)
async def handle_channel_post(message: Message):
    """Channel posts arrive as channel_post updates, not message."""
    await auto_translate(message)


async def auto_translate(message: Message):
    """
    Auto-translate between Polish and Ukrainian.
    Detects language and translates automatically.
    Uses the last HISTORY_SIZE chat messages as context.
    """
    chat_id = message.chat.id
    # Channels have no from_user - rate limit per chat instead
    user_id = message.from_user.id if message.from_user else chat_id
    text = (message.text or "").strip()

    # Skip commands (they start with /)
    if not text or text.startswith("/"):
        return

    author = get_author(message)
    context = get_history(chat_id)
    add_history(chat_id, author, text)

    # Check rate limit
    allowed, minutes = rate_limiter.check(user_id)
    if not allowed:
        logger.warning(f"Rate limit hit for {user_id} in chat {chat_id}")
        return

    rate_limiter.record(user_id)

    # Typing indicator
    await message.bot.send_chat_action(chat_id, ChatAction.TYPING)

    try:
        # Use the default pair (pl, uk) for auto-translation
        lang_pair = DEFAULT_LANG_PAIR

        # Detect the language of the input text
        detected_lang = detect_language(text)
        target_lang = "uk" if detected_lang == "pl" else "pl"

        result = await translate_text_with_context(
            text,
            lang_pair,
            context,
            detected_lang
        )
        translation = result.get("translation", "").strip()
        if not translation:
            return

        source_flag = SUPPORTED_LANGUAGES[detected_lang]["flag"]
        target_flag = SUPPORTED_LANGUAGES[target_lang]["flag"]
        response = f"{source_flag}→{target_flag} {html.escape(translation)}"

        await message.reply(response)

    except Exception as e:
        logger.error(f"Error auto-translating text in chat {chat_id}: {e}")
