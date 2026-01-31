"""
AI service - audio transcription + translation using Google Gemini API.
Single API call for STT + translation (faster than Whisper).
"""
import json
import re
import logging
import asyncio

import google.generativeai as genai

from config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Model configuration
MODEL_NAME = "gemini-2.0-flash"

# Prompts (ultra-short for speed)
VOICE_PROMPT = """Transcribe and translate EN↔KM audio.
Return JSON only: {"lang":"en","text":"...","translation":"..."}"""

TEXT_PROMPT = """Translate EN↔KM.
Return JSON only: {"from":"en","to":"km","translation":"..."}
Text: """


def parse_json_response(response_text: str) -> dict:
    """Parse JSON response, handling markdown code blocks."""
    text = response_text.strip()
    
    # Remove markdown code blocks
    if text.startswith("```"):
        # Find the end of code block
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
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
    
    # Try to find JSON object in text
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


async def translate_audio(audio_path: str) -> dict:
    """
    Transcribe and translate audio using Gemini (single API call).
    
    Args:
        audio_path: Path to audio file (OGG, MP3, etc.)
        
    Returns:
        Dict with 'lang', 'text', 'translation'
    """
    logger.info(f"Processing audio: {audio_path}")
    
    loop = asyncio.get_event_loop()
    
    # Upload file to Gemini with explicit mime_type
    def upload_with_mime():
        return genai.upload_file(audio_path, mime_type="audio/ogg")
    
    audio_file = await loop.run_in_executor(None, upload_with_mime)
    
    # Generate
    model = genai.GenerativeModel(MODEL_NAME)
    
    def _generate():
        return model.generate_content([VOICE_PROMPT, audio_file])
    
    response = await loop.run_in_executor(None, _generate)
    
    # Cleanup uploaded file (sync, non-blocking error handling)
    try:
        audio_file.delete()
    except Exception as e:
        logger.warning(f"Failed to delete uploaded file: {e}")
    
    result = parse_json_response(response.text)
    logger.info(f"Audio result: lang={result.get('lang')}, text={result.get('text', '')[:30]}...")
    
    return result


async def translate_text(text: str, source_lang: str = None) -> dict:
    """
    Translate text using Gemini.
    
    Args:
        text: Text to translate
        source_lang: Optional source language hint
        
    Returns:
        Dict with 'from', 'to', 'translation'
    """
    logger.info(f"Translating: {text[:50]}...")
    
    model = genai.GenerativeModel(MODEL_NAME)
    loop = asyncio.get_event_loop()
    
    prompt = TEXT_PROMPT
    if source_lang:
        prompt = f"From {source_lang}. " + prompt
    
    def _generate():
        return model.generate_content(prompt + text)
    
    response = await loop.run_in_executor(None, _generate)
    
    result = parse_json_response(response.text)
    logger.info(f"Translation: {result.get('from')} -> {result.get('to')}")
    
    return result


# Alias for backward compatibility
async def translate(text: str, source_lang: str = None) -> dict:
    return await translate_text(text, source_lang)
