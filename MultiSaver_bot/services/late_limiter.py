import time
from collections import defaultdict
from typing import Dict, List

from config import get_settings
from utils.errors import RateLimitError


class RateLimiter:
    """Sliding-window rate limiter."""

    def __init__(self) -> None:
        settings = get_settings()
        self.max_requests = settings.rate_limit_requests
        self.period = settings.rate_limit_period
        self._hits: Dict[int, List[float]] = defaultdict(list)

    def _cleanup(self, user_id: int, now: float) -> None:
        cutoff = now - self.period
        self._hits[user_id] = [t for t in self._hits[user_id] if t > cutoff]

    def check(self, user_id: int) -> None:
        """Raise RateLimitError if limit exceeded."""
        now = time.monotonic()
        self._cleanup(user_id, now)
        if len(self._hits[user_id]) >= self.max_requests:
            oldest = min(self._hits[user_id])
            wait = int(self.period - (now - oldest)) + 1
            raise RateLimitError(seconds=max(wait, 1))
        self._hits[user_id].append(now)

    def remaining(self, user_id: int) -> int:
        now = time.monotonic()
        self._cleanup(user_id, now)
        return max(0, self.max_requests - len(self._hits[user_id]))


_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter
