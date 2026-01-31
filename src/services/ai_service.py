"""
AI service - audio transcription + translation using Google Gemini API.
Uses inline base64 audio for reliable processing.
Supports dynamic language pairs.
"""
import json
import base64
import logging
import aiohttp

from config import GOOGLE_API_KEY, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"


def get_lang_name(code: str) -> str:
    """Get language name from code."""
    return SUPPORTED_LANGUAGES.get(code, {}).get("name", code)


def build_voice_prompt(lang_pair: tuple) -> str:
    """Build voice prompt for specific language pair."""
    lang1, lang2 = lang_pair
    name1 = get_lang_name(lang1)
    name2 = get_lang_name(lang2)
    
    return f"""You are a translator for {name1} and {name2}.
Task:
1. Listen to the audio and transcribe what is spoken.
2. Detect if the language is {name1} ('{lang1}') or {name2} ('{lang2}').
3. Translate it to the other language ({lang1.upper()}→{lang2.upper()} or {lang2.upper()}→{lang1.upper()}).

Return ONLY a JSON object with no markdown:
{{"lang":"{lang1}","text":"transcribed text","translation":"translated text"}}"""


def build_text_prompt(lang_pair: tuple) -> str:
    """Build text prompt for specific language pair."""
    lang1, lang2 = lang_pair
    name1 = get_lang_name(lang1)
    name2 = get_lang_name(lang2)
    
    return f"""You are a translator for {name1} and {name2}.
Task:
1. Detect if the input text is {name1} ('{lang1}') or {name2} ('{lang2}').
2. Translate it to the other language.

Return ONLY a JSON object with no markdown:
{{"from":"{lang1}","to":"{lang2}","translation":"translated text"}}

Text: """


def parse_json_response(response_text: str) -> dict:
    """Parse JSON response, handling markdown code blocks."""
    text = response_text.strip()
    
    # Remove markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        content_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            elif line.startswith("```") and in_block:
                break
            elif in_block:
                content_lines.append(line)
        text = "\n".join(content_lines)
    
    text = text.strip()
    
    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    
    if start != -1 and end != -1:
        text = text[start:end+1]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}, text: {text[:100]}")
        raise ValueError(f"Parse error: {e}")


async def translate_audio(audio_path: str, lang_pair: tuple = ("en", "km")) -> dict:
    """
    Transcribe and translate audio using Gemini with inline base64.
    
    Args:
        audio_path: Path to audio file (OGG, MP3, etc.)
        lang_pair: Tuple of (lang1, lang2) for translation
        
    Returns:
        Dict with 'lang', 'text', 'translation'
    """
    logger.info(f"Processing audio: {audio_path}, pair: {lang_pair}")
    
    # Read and encode audio as base64
    with open(audio_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Build dynamic prompt
    prompt = build_voice_prompt(lang_pair)
    
    # Prepare request
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "audio/ogg",
                        "data": audio_data
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
        }
    }
    
    # Make async HTTP request
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}?key={GOOGLE_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"API error {response.status}: {error_text[:200]}")
                raise ValueError(f"API error: {response.status}")
            
            data = await response.json()
    
    # Extract text from response
    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    
    result = parse_json_response(text)
    logger.info(f"Audio result: lang={result.get('lang')}, text={result.get('text', '')[:30]}...")
    
    return result


async def translate_text(text: str, lang_pair: tuple = ("en", "km")) -> dict:
    """
    Translate text using Gemini.
    
    Args:
        text: Text to translate
        lang_pair: Tuple of (lang1, lang2) for translation
        
    Returns:
        Dict with 'from', 'to', 'translation'
    """
    logger.info(f"Translating: {text[:50]}..., pair: {lang_pair}")
    
    # Build dynamic prompt
    prompt = build_text_prompt(lang_pair)
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt + text}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}?key={GOOGLE_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"API error {response.status}: {error_text[:200]}")
                raise ValueError(f"API error: {response.status}")
            
            data = await response.json()
    
    text_response = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    
    result = parse_json_response(text_response)
    logger.info(f"Translation: {result.get('from')} -> {result.get('to')}")
    
    return result


# Alias for backward compatibility
async def translate(text: str, lang_pair: tuple = ("en", "km")) -> dict:
    return await translate_text(text, lang_pair)
