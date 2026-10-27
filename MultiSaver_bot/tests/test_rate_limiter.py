
import pytest

from services.rate_limiter import RateLimiter
from utils.errors import RateLimitError


def test_allows_under_limit():
    limiter = RateLimiter()
    limiter.max_requests = 3
    limiter.period = 60
    for _ in range(3):
        limiter.check(42)
    assert limiter.remaining(42) == 0


def test_blocks_over_limit():
    limiter = RateLimiter()
    limiter.max_requests = 2
    limiter.period = 60
    limiter.check(99)
    limiter.check(99)
    with pytest.raises(RateLimitError):
        limiter.check(99)
