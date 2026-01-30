"""
Audio service - handles audio file conversion and temp folder cleanup.
"""
import os
import time
import logging
from pathlib import Path

from pydub import AudioSegment

from config import TEMP_DIR, TEMP_CLEANUP_AFTER_FILES, MAX_AUDIO_DURATION_SECONDS

logger = logging.getLogger(__name__)

# Counter for processed files (triggers cleanup)
_processed_files_count = 0


def ensure_temp_dir() -> None:
    """Ensure temp directory exists."""
    os.makedirs(TEMP_DIR, exist_ok=True)


def convert_oga_to_mp3(oga_path: str) -> str:
    """
    Convert OGA (Telegram voice) to MP3 format.
    
    Args:
        oga_path: Path to the OGA file
        
    Returns:
        Path to the converted MP3 file
    """
    ensure_temp_dir()
    
    mp3_path = oga_path.replace(".oga", ".mp3")
    
    audio = AudioSegment.from_file(oga_path, format="ogg")
    audio.export(mp3_path, format="mp3")
    
    logger.debug(f"Converted {oga_path} to {mp3_path}")
    return mp3_path


def get_audio_duration(file_path: str) -> float:
    """
    Get audio duration in seconds.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000.0  # pydub uses milliseconds


def check_audio_duration(file_path: str) -> tuple[bool, float]:
    """
    Check if audio duration is within limits.
    
    Returns:
        Tuple of (is_valid, duration_seconds)
    """
    duration = get_audio_duration(file_path)
    is_valid = duration <= MAX_AUDIO_DURATION_SECONDS
    return is_valid, duration


def cleanup_temp_files(force: bool = False) -> int:
    """
    Clean up old temporary files.
    
    Args:
        force: If True, cleanup regardless of counter
        
    Returns:
        Number of files deleted
    """
    global _processed_files_count
    
    _processed_files_count += 1
    
    # Only cleanup every N processed files (unless forced)
    if not force and _processed_files_count < TEMP_CLEANUP_AFTER_FILES:
        return 0
    
    _processed_files_count = 0
    deleted_count = 0
    cutoff_time = time.time() - 300  # 5 minutes ago
    
    try:
        for file_path in Path(TEMP_DIR).glob("*"):
            if file_path.is_file():
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old temp file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning temp files: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} temp files")
    
    return deleted_count


def delete_file(file_path: str) -> None:
    """Safely delete a file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
