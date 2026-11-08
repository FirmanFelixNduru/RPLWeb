"""
CompareBuy — SEC-008 Phase 2 (W1): Application-Level Rate Limiter
In-memory Token Bucket rate limiter protecting price lookup endpoints.
"""
from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import HTTPException, Request

from app.security.client_ip import ClientIPResolutionError, resolve_client_ip

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of a rate limiter consumption request."""
    allowed: bool
    retry_after: int
    remaining: int = 0


@dataclass
class _BucketState:
    """Internal mutable state for a single client IP bucket."""
    tokens: float
    last_updated: float


class TokenBucketRateLimiter:
    """Thread-safe in-memory Token Bucket rate limiter with bounded memory.

    Parameters:
        capacity: Maximum burst tokens per IP bucket (default: 5.0).
        refill_rate_per_minute: Number of tokens added per minute (default: 10.0).
        max_entries: Hard upper bound on tracked client IPs to prevent memory exhaustion (default: 10,000).
        clock_fn: Monotonic time provider, customizable for deterministic testing (default: time.monotonic).
    """

    def __init__(
        self,
        capacity: float = 5.0,
        refill_rate_per_minute: float = 10.0,
        max_entries: int = 10000,
        clock_fn: Callable[[], float] = time.monotonic,
        log_cooldown_seconds: float = 60.0,
    ) -> None:
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_minute) / 60.0  # tokens per second (e.g. 1/6)
        self.max_entries = int(max_entries)
        self.clock_fn = clock_fn
        self.log_cooldown_seconds = float(log_cooldown_seconds)

        # Time in seconds for an empty bucket to completely refill to full capacity
        self._idle_timeout = self.capacity / self.refill_rate

        self._buckets: dict[str, _BucketState] = {}
        self._lock = threading.Lock()
        self._cleanup_counter = 0
        self._last_capacity_log_time: float = float("-inf")
        self._suppressed_capacity_logs: int = 0

    def consume(self, client_ip: str) -> RateLimitResult:
        """Attempt to consume 1 token for the specified client IP.

        Thread-safe: critical section is protected by self._lock and contains
        only non-blocking mathematical calculations.
        """
        if not client_ip or not isinstance(client_ip, str):
            return RateLimitResult(allowed=False, retry_after=int(math.ceil(self._idle_timeout)), remaining=0)

        with self._lock:
            now = self.clock_fn()

            if client_ip in self._buckets:
                state = self._buckets[client_ip]
                # Defend against monotonic clock stepping backward
                elapsed = max(0.0, now - state.last_updated)
                # Refill tokens up to maximum capacity
                state.tokens = min(self.capacity, state.tokens + elapsed * self.refill_rate)
                state.last_updated = now
            else:
                # Registry capacity check before adding a new IP entry
                if len(self._buckets) >= self.max_entries:
                    self._cleanup_idle_buckets_locked(now)
                    if len(self._buckets) >= self.max_entries:
                        should_log = False
                        suppressed_count = 0
                        if (now - self._last_capacity_log_time) >= self.log_cooldown_seconds:
                            should_log = True
                            self._last_capacity_log_time = now
                            suppressed_count = self._suppressed_capacity_logs
                            self._suppressed_capacity_logs = 0
                        else:
                            self._suppressed_capacity_logs += 1

                        if should_log:
                            if suppressed_count > 0:
                                logger.warning(
                                    "Rate limiter registry capacity reached (%d entries). Rejecting new requests. Suppressed events: %d.",
                                    self.max_entries,
                                    suppressed_count,
                                )
                            else:
                                logger.warning(
                                    "Rate limiter registry capacity reached (%d entries). Rejecting new requests.",
                                    self.max_entries,
                                )
                        return RateLimitResult(
                            allowed=False,
                            retry_after=int(math.ceil(self._idle_timeout)),
                            remaining=0,
                        )

                # Initialize new bucket with full capacity
                state = _BucketState(tokens=self.capacity, last_updated=now)
                self._buckets[client_ip] = state

            # Periodic background cleanup of idle full buckets
            self._cleanup_counter += 1
            if self._cleanup_counter >= 100:
                self._cleanup_counter = 0
                self._cleanup_idle_buckets_locked(now)

            # Evaluate token availability
            if state.tokens >= 1.0:
                state.tokens -= 1.0
                return RateLimitResult(
                    allowed=True,
                    retry_after=0,
                    remaining=int(math.floor(state.tokens)),
                )
            else:
                # Calculate exact seconds until at least 1 token is available (with float precision rounding)
                missing = 1.0 - state.tokens
                retry_after = max(1, int(math.ceil(round(missing / self.refill_rate, 9))))
                return RateLimitResult(
                    allowed=False,
                    retry_after=retry_after,
                    remaining=0,
                )

    def _cleanup_idle_buckets_locked(self, now: float) -> int:
        """Evict only buckets that have been idle long enough to have refilled to full capacity.

        Active / depleted buckets are NEVER evicted to prevent attackers from clearing
        their depleted quota through registry churn.
        Must be called while holding self._lock.
        """
        evict_keys = [
            ip for ip, state in self._buckets.items()
            if (now - state.last_updated) >= self._idle_timeout
        ]
        for ip in evict_keys:
            del self._buckets[ip]
        return len(evict_keys)

    def reset(self) -> None:
        """Clear all active buckets. Primarily used in test teardowns."""
        with self._lock:
            self._buckets.clear()
            self._cleanup_counter = 0
            self._last_capacity_log_time = float("-inf")
            self._suppressed_capacity_logs = 0


# Default global rate limiter instance for CompareBuy price endpoints
price_rate_limiter = TokenBucketRateLimiter(
    capacity=5.0,
    refill_rate_per_minute=10.0,
    max_entries=10000,
)


def check_price_rate_limit(request: Request) -> str:
    """FastAPI dependency to resolve client IP and enforce W1 rate limit.

    Returns:
        Canonical client IP string if request is within quota.

    Raises:
        HTTPException(400): If client IP cannot be securely resolved.
        HTTPException(429): If client IP has exceeded the rate limit.
    """
    try:
        client_ip = resolve_client_ip(request)
    except ClientIPResolutionError:
        # In local development test runners (e.g. Starlette TestClient with client.host='testclient')
        from app.security.client_ip import is_render_runtime
        if not is_render_runtime() and getattr(request.client, "host", None) == "testclient":
            client_ip = "127.0.0.1"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid or missing client identity headers.",
            )

    result = price_rate_limiter.consume(client_ip)
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": str(result.retry_after),
                "Cache-Control": "no-store",
            },
        )

    return client_ip
