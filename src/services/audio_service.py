"""
Audio service - handles audio file processing and temp folder cleanup.
Optimized: skip MP3 conversion, lower quality, async cleanup.
"""
import os
import time
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from pydub import AudioSegment

from config import TEMP_DIR, TEMP_CLEANUP_AFTER_FILES, MAX_AUDIO_DURATION_SECONDS

logger = logging.getLogger(__name__)

# Counter for processed files (triggers cleanup)
_processed_files_count = 0

# Thread pool for background file operations
_executor = ThreadPoolExecutor(max_workers=2)


def ensure_temp_dir() -> None:
    """Ensure temp directory exists."""
    os.makedirs(TEMP_DIR, exist_ok=True)


def compress_audio(input_path: str) -> str:
    """
    Compress audio for faster processing (no format conversion).
    
    Optimizations:
    - 8kHz sample rate (telephone quality, sufficient for speech)
    - Mono channel
    - Keeps OGG format (no conversion needed)
    
    Args:
        input_path: Path to the audio file
        
    Returns:
        Path to compressed audio (same path if no compression needed)
    """
    ensure_temp_dir()
    
    output_path = input_path.replace(".oga", "_compressed.ogg")
    
    try:
        audio = AudioSegment.from_file(input_path)
        
        # Check if compression is beneficial
        original_size = os.path.getsize(input_path)
        
        # Convert to mono, low sample rate
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(8000)  # 8kHz - telephone quality
        
        # Export as OGG (Whisper accepts it directly)
        audio.export(
            output_path,
            format="ogg",
            parameters=["-q:a", "0"]  # Lowest quality/fastest
        )
        
        compressed_size = os.path.getsize(output_path)
        logger.debug(f"Compressed {original_size} -> {compressed_size} bytes")
        
        return output_path
        
    except Exception as e:
        logger.warning(f"Compression failed, using original: {e}")
        return input_path


def get_audio_duration_fast(file_path: str) -> float:
    """
    Get audio duration quickly using file metadata.
    Falls back to full load if needed.
    """
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0
    except Exception as e:
        logger.warning(f"Could not get duration: {e}")
        return 0.0


def check_audio_duration(file_path: str) -> tuple[bool, float]:
    """
    Check if audio duration is within limits.
    
    Returns:
        Tuple of (is_valid, duration_seconds)
    """
    duration = get_audio_duration_fast(file_path)
    is_valid = duration <= MAX_AUDIO_DURATION_SECONDS
    return is_valid, duration


def _sync_cleanup_temp_files() -> int:
    """Synchronous cleanup for thread pool execution."""
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


def cleanup_temp_files_async() -> None:
    """Trigger async cleanup in background (non-blocking)."""
    global _processed_files_count
    
    _processed_files_count += 1
    
    if _processed_files_count < TEMP_CLEANUP_AFTER_FILES:
        return
    
    _processed_files_count = 0
    _executor.submit(_sync_cleanup_temp_files)


def cleanup_temp_files(force: bool = False) -> int:
    """Clean up old temporary files."""
    if not force:
        cleanup_temp_files_async()
        return 0
    return _sync_cleanup_temp_files()


def _sync_delete_file(file_path: str) -> None:
    """Synchronous file deletion."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")


def delete_file(file_path: str) -> None:
    """Safely delete a file (non-blocking)."""
    _executor.submit(_sync_delete_file, file_path)


def delete_files(*file_paths: str) -> None:
    """Delete multiple files (non-blocking)."""
    for path in file_paths:
        if path:
            _executor.submit(_sync_delete_file, path)
