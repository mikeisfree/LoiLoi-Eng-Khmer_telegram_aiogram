"""
Rate limiter - simple per-user request limiting.
"""
import time
from collections import defaultdict
from typing import Tuple

from config import MAX_REQUESTS_PER_USER_PER_HOUR


class RateLimiter:
    """Simple in-memory rate limiter per user."""
    
    def __init__(self, max_requests: int = MAX_REQUESTS_PER_USER_PER_HOUR, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # user_id -> list of timestamps
        self._requests: dict[int, list[float]] = defaultdict(list)
    
    def _cleanup_old_requests(self, user_id: int) -> None:
        """Remove requests older than the time window."""
        cutoff = time.time() - self.window_seconds
        self._requests[user_id] = [
            ts for ts in self._requests[user_id] if ts > cutoff
        ]
    
    def check(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user can make a request.
        
        Returns:
            Tuple of (allowed: bool, minutes_until_reset: int)
        """
        self._cleanup_old_requests(user_id)
        
        if len(self._requests[user_id]) >= self.max_requests:
            # Calculate time until oldest request expires
            oldest = min(self._requests[user_id])
            seconds_until_reset = int((oldest + self.window_seconds) - time.time())
            minutes_until_reset = max(1, seconds_until_reset // 60)
            return False, minutes_until_reset
        
        return True, 0
    
    def record(self, user_id: int) -> None:
        """Record a request for the user."""
        self._requests[user_id].append(time.time())


# Global rate limiter instance
rate_limiter = RateLimiter()
