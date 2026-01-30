"""
AI service - communication with Google Gemini API.
"""
import json
import re
import logging
from typing import Optional

import google.generativeai as genai

from config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Model configuration
MODEL_NAME = "gemini-2.0-flash"

# Prompts
VOICE_PROMPT = """You are a simultaneous interpreter for English and Khmer (Cambodian).
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
}"""

TEXT_PROMPT = """You are a translator for English and Khmer (Cambodian).
Task:
1. Detect if the input text is English ('en') or Khmer ('km').
2. Translate it to the other language.

Output format: Return ONLY a raw JSON object (no markdown, no code blocks).
{
    "detected_lang": "en",
    "original": "Input text...",
    "translation": "Translated text..."
}

Text to translate:
"""


def parse_gemini_response(response_text: str) -> dict:
    """
    Parse Gemini response, removing markdown if present.
    
    Args:
        response_text: Raw response from Gemini
        
    Returns:
        Parsed JSON dict
        
    Raises:
        ValueError: If parsing fails
    """
    # Remove markdown code blocks if present
    cleaned = response_text.strip()
    cleaned = re.sub(r'^```json\s*', '', cleaned)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response: {response_text[:200]}")
        raise ValueError(f"Failed to parse AI response: {e}")


async def translate_audio(audio_path: str) -> dict:
    """
    Transcribe and translate audio using Gemini.
    
    Args:
        audio_path: Path to the MP3 audio file
        
    Returns:
        Dict with detected_lang, transcription, translation
    """
    logger.info(f"Processing audio file: {audio_path}")
    
    # Upload file to Gemini
    audio_file = genai.upload_file(audio_path)
    
    # Create model and generate
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content([VOICE_PROMPT, audio_file])
    
    # Clean up uploaded file
    try:
        audio_file.delete()
    except Exception as e:
        logger.warning(f"Failed to delete uploaded file: {e}")
    
    result = parse_gemini_response(response.text)
    logger.info(f"Audio translation result: lang={result.get('detected_lang')}")
    
    return result


async def translate_text(text: str) -> dict:
    """
    Translate text using Gemini.
    
    Args:
        text: Text to translate
        
    Returns:
        Dict with detected_lang, original, translation
    """
    logger.info(f"Translating text: {text[:50]}...")
    
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(TEXT_PROMPT + text)
    
    result = parse_gemini_response(response.text)
    logger.info(f"Text translation result: lang={result.get('detected_lang')}")
    
    return result
