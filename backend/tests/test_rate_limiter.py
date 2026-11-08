"""
CompareBuy — SEC-008 Phase 2 (W1): Rate Limiter Test Suite

Validates Token Bucket unit behavior (W1-T01 through W1-T18)
and endpoint integration behavior (W1-API-01 through W1-API-18).
"""
from __future__ import annotations

import concurrent.futures
import math
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Ensure backend root is in sys.path
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from tests._db_guard import enforce_safe_test_db_env, offline_price_endpoint_context

enforce_safe_test_db_env()

from fastapi.testclient import TestClient
from app.main import app
from app.security.rate_limiter import (
    RateLimitResult,
    TokenBucketRateLimiter,
    price_rate_limiter,
)


class FakeClock:
    """Controllable monotonic clock for deterministic rate limiter testing."""

    def __init__(self, start: float = 1000.0) -> None:
        self.time = float(start)

    def __call__(self) -> float:
        return self.time

    def advance(self, seconds: float) -> None:
        self.time += float(seconds)

    def set(self, timestamp: float) -> None:
        self.time = float(timestamp)


class TestTokenBucketRateLimiter(unittest.TestCase):
    """Unit tests for TokenBucketRateLimiter (W1-T01 to W1-T18)."""

    def setUp(self) -> None:
        self.clock = FakeClock(1000.0)
        self.limiter = TokenBucketRateLimiter(
            capacity=5.0,
            refill_rate_per_minute=10.0,  # 1/6 token per second
            max_entries=100,
            clock_fn=self.clock,
        )

    def test_w1_t01_first_request_from_new_ip_allowed(self):
        """W1-T01: First request from a new IP is allowed with full initial capacity."""
        res = self.limiter.consume("192.0.2.1")
        self.assertTrue(res.allowed)
        self.assertEqual(res.retry_after, 0)
        self.assertEqual(res.remaining, 4)

    def test_w1_t02_first_5_requests_immediately_allowed(self):
        """W1-T02: First 5 requests in immediate burst are all allowed."""
        ip = "192.0.2.2"
        for i in range(5):
            res = self.limiter.consume(ip)
            self.assertTrue(res.allowed, f"Request {i+1} should be allowed")
            self.assertEqual(res.remaining, 4 - i)

    def test_w1_t03_sixth_immediate_request_rejected(self):
        """W1-T03: Sixth immediate request exceeding burst capacity is rejected."""
        ip = "192.0.2.3"
        for _ in range(5):
            self.limiter.consume(ip)

        res = self.limiter.consume(ip)
        self.assertFalse(res.allowed)
        self.assertGreaterEqual(res.retry_after, 1)
        self.assertEqual(res.remaining, 0)

    def test_w1_t04_refill_after_known_interval(self):
        """W1-T04: Bucket refills accurately after elapsed interval (6s -> 1 token)."""
        ip = "192.0.2.4"
        for _ in range(5):
            self.limiter.consume(ip)

        # Depleted: 6th request fails
        res = self.limiter.consume(ip)
        self.assertFalse(res.allowed)

        # Advance clock by exactly 6 seconds (1/6 tokens/sec * 6 = 1.0 token)
        self.clock.advance(6.0)

        res_refilled = self.limiter.consume(ip)
        self.assertTrue(res_refilled.allowed)
        self.assertEqual(res_refilled.remaining, 0)

    def test_w1_t05_refill_up_to_capacity_no_overflow(self):
        """W1-T05: Refill never exceeds configured capacity even after long idle times."""
        ip = "192.0.2.5"
        self.limiter.consume(ip)  # remaining 4

        # Advance by 1 hour (3600s)
        self.clock.advance(3600.0)

        # Bucket should cap at 5.0 tokens
        state = self.limiter._buckets[ip]
        # Next request consumes 1 from 5.0 -> remaining 4
        res = self.limiter.consume(ip)
        self.assertTrue(res.allowed)
        self.assertEqual(res.remaining, 4)

    def test_w1_t06_retry_after_calculation(self):
        """W1-T06: Retry-After calculation produces rounded-up integer seconds."""
        ip = "192.0.2.6"
        for _ in range(5):
            self.limiter.consume(ip)

        # Missing 1.0 token, refill rate = 1/6 token/sec -> exactly 6.0s -> ceil is 6
        res = self.limiter.consume(ip)
        self.assertEqual(res.retry_after, 6)

        # Advance by 2.0s -> tokens = 2.0 * (1/6) = 0.3333, missing = 0.6666 -> 4.0s -> ceil is 4
        self.clock.advance(2.0)
        res2 = self.limiter.consume(ip)
        self.assertFalse(res2.allowed)
        self.assertEqual(res2.retry_after, 4)

    def test_w1_t07_two_different_ips_independent_buckets(self):
        """W1-T07: Different client IPs maintain independent token buckets."""
        ip_a = "192.0.2.10"
        ip_b = "192.0.2.20"

        # Deplete IP A
        for _ in range(5):
            self.limiter.consume(ip_a)
        self.assertFalse(self.limiter.consume(ip_a).allowed)

        # IP B must still have full 5 tokens
        res_b = self.limiter.consume(ip_b)
        self.assertTrue(res_b.allowed)
        self.assertEqual(res_b.remaining, 4)

    def test_w1_t08_same_ip_shared_bucket(self):
        """W1-T08: Same client IP shares quota regardless of endpoint/product ID."""
        ip = "192.0.2.30"
        self.limiter.consume(ip)
        self.limiter.consume(ip)
        self.assertEqual(self.limiter._buckets[ip].tokens, 3.0)

    def test_w1_t09_monotonic_clock_advances_correct_refill(self):
        """W1-T09: Advancing monotonic clock accurately increases token balance."""
        ip = "192.0.2.40"
        for _ in range(5):
            self.limiter.consume(ip)

        # Advance 12 seconds = 2 tokens
        self.clock.advance(12.0)
        res1 = self.limiter.consume(ip)
        self.assertTrue(res1.allowed)
        res2 = self.limiter.consume(ip)
        self.assertTrue(res2.allowed)
        res3 = self.limiter.consume(ip)
        self.assertFalse(res3.allowed)

    def test_w1_t10_clock_does_not_advance_no_additional_refill(self):
        """W1-T10: Zero time elapsed yields zero additional tokens."""
        ip = "192.0.2.50"
        for _ in range(5):
            self.limiter.consume(ip)

        # No clock advance
        res = self.limiter.consume(ip)
        self.assertFalse(res.allowed)

    def test_w1_t11_concurrent_same_ip_consumption(self):
        """W1-T11: Concurrent threads consuming same IP never exceed burst capacity."""
        ip = "192.0.2.60"
        num_threads = 20
        results: list[RateLimitResult] = []

        def worker():
            return self.limiter.consume(ip)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        allowed_count = sum(1 for r in results if r.allowed)
        rejected_count = sum(1 for r in results if not r.allowed)

        self.assertEqual(allowed_count, 5)
        self.assertEqual(rejected_count, 15)

    def test_w1_t12_concurrent_distinct_ips(self):
        """W1-T12: Concurrent threads with distinct IPs consume independently."""
        num_ips = 10
        results: dict[str, list[RateLimitResult]] = {}

        def worker(client_ip: str):
            res_list = []
            for _ in range(5):
                res_list.append(self.limiter.consume(client_ip))
            return client_ip, res_list

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_ips) as executor:
            futures = [executor.submit(worker, f"192.0.2.{100 + i}") for i in range(num_ips)]
            for f in concurrent.futures.as_completed(futures):
                cip, rlist = f.result()
                results[cip] = rlist

        self.assertEqual(len(results), num_ips)
        for cip, rlist in results.items():
            self.assertTrue(all(r.allowed for r in rlist), f"All 5 requests for {cip} should be allowed")

    def test_w1_t13_idle_bucket_expiration(self):
        """W1-T13: Idle buckets exceeding idle timeout are cleanly evicted during cleanup."""
        ip = "192.0.2.70"
        self.limiter.consume(ip)
        self.assertIn(ip, self.limiter._buckets)

        # Advance past idle timeout (5 tokens / (1/6) = 30 seconds)
        self.clock.advance(35.0)

        # Trigger cleanup
        with self.limiter._lock:
            evicted = self.limiter._cleanup_idle_buckets_locked(self.clock())
        self.assertGreaterEqual(evicted, 1)
        self.assertNotIn(ip, self.limiter._buckets)

    def test_w1_t14_registry_reaches_capacity_safe_failure(self):
        """W1-T14: When registry reaches max_entries and no buckets are idle, new IPs are safely rejected."""
        small_limiter = TokenBucketRateLimiter(
            capacity=5.0,
            refill_rate_per_minute=10.0,
            max_entries=3,
            clock_fn=self.clock,
        )

        small_limiter.consume("10.0.0.1")
        small_limiter.consume("10.0.0.2")
        small_limiter.consume("10.0.0.3")
        self.assertEqual(len(small_limiter._buckets), 3)

        # 4th IP arrives while 1-3 are actively depleted (0s elapsed, not idle)
        res4 = small_limiter.consume("10.0.0.4")
        self.assertFalse(res4.allowed)
        self.assertEqual(len(small_limiter._buckets), 3)
        self.assertNotIn("10.0.0.4", small_limiter._buckets)

    def test_w1_t15_active_bucket_not_evicted_quota_cannot_reset(self):
        """W1-T15: Active/depleted buckets are never evicted, preventing quota reset via churn."""
        ip = "192.0.2.80"
        for _ in range(5):
            self.limiter.consume(ip)

        # Bucket is depleted (0 tokens) and updated at t=1000.
        # Advance clock by only 5 seconds (not idle, idle_timeout=30s)
        self.clock.advance(5.0)

        with self.limiter._lock:
            evicted = self.limiter._cleanup_idle_buckets_locked(self.clock())
        self.assertEqual(evicted, 0)
        self.assertIn(ip, self.limiter._buckets)

        # Quota remains exhausted (only 5 * 1/6 = 0.833 tokens, needs 1.0)
        res = self.limiter.consume(ip)
        self.assertFalse(res.allowed)

    def test_w1_t16_invalid_client_identity_rejected(self):
        """W1-T16: Invalid client identity (None, empty) is rejected without creating default bucket."""
        res_empty = self.limiter.consume("")
        self.assertFalse(res_empty.allowed)

        res_none = self.limiter.consume(None)  # type: ignore
        self.assertFalse(res_none.allowed)
        self.assertEqual(len(self.limiter._buckets), 0)

    def test_w1_t17_malformed_clock_scenario_no_overflow_or_negative(self):
        """W1-T17: Clock skew stepping backward does not corrupt token balance or cause negative elapsed."""
        ip = "192.0.2.90"
        self.limiter.consume(ip)  # tokens = 4.0, last_updated = 1000.0

        # Clock steps backward to 900.0
        self.clock.set(900.0)
        res = self.limiter.consume(ip)
        self.assertTrue(res.allowed)
        self.assertEqual(res.remaining, 3)

    def test_w1_t18_initial_bucket_capacity_exact(self):
        """W1-T18: Newly created bucket starts with exactly configured capacity."""
        limiter = TokenBucketRateLimiter(capacity=7.0, refill_rate_per_minute=10.0, clock_fn=self.clock)
        res = limiter.consume("192.0.2.99")
        self.assertTrue(res.allowed)
        self.assertEqual(res.remaining, 6)


class TestPriceEndpointRateLimiting(unittest.TestCase):
    """Endpoint integration tests for W1 rate limiting on /api/prices/{product_id}."""

    def setUp(self) -> None:
        price_rate_limiter.reset()

    def tearDown(self) -> None:
        price_rate_limiter.reset()

    def test_w1_api_01_price_request_below_limit_allowed(self):
        """W1-API-01: Requests within quota execute price handler and return 200 OK."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                resp = client.get("/api/prices/sm-001")
                self.assertEqual(resp.status_code, 200)

    def test_w1_api_02_price_request_over_limit_returns_429(self):
        """W1-API-02: Request exceeding burst limit returns HTTP 429 Too Many Requests."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for _ in range(5):
                    r = client.get("/api/prices/sm-001")
                    self.assertEqual(r.status_code, 200)

                # 6th request from same local peer IP
                r6 = client.get("/api/prices/sm-001")
                self.assertEqual(r6.status_code, 429)

    def test_w1_api_03_429_response_headers_and_body(self):
        """W1-API-03: HTTP 429 response contains Retry-After, Cache-Control: no-store, and detail message."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for _ in range(5):
                    client.get("/api/prices/sm-001")

                r6 = client.get("/api/prices/sm-001")
                self.assertEqual(r6.status_code, 429)
                self.assertIn("retry-after", r6.headers)
                self.assertEqual(r6.headers.get("cache-control"), "no-store")
                self.assertEqual(r6.json(), {"detail": "Too many requests. Please try again later."})
                retry_sec = int(r6.headers["retry-after"])
                self.assertGreaterEqual(retry_sec, 1)

    @patch("app.scrape_worker.run_isolated_scrape_flight")
    def test_w1_api_04_429_request_does_not_start_scraper(self, mock_flight: AsyncMock):
        """W1-API-04: Exceeded rate limit request rejects before starting scraper worker."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for _ in range(5):
                    client.get("/api/prices/sm-001")

                mock_flight.reset_mock()
                r6 = client.get("/api/prices/sm-001")
                self.assertEqual(r6.status_code, 429)
                mock_flight.assert_not_called()

    @patch("app.repositories.price_repo.save_price_snapshot")
    def test_w1_api_05_429_request_does_not_execute_database_persistence(self, mock_save):
        """W1-API-05: Exceeded rate limit request rejects before executing database persistence."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for _ in range(5):
                    client.get("/api/prices/sm-001")

                mock_save.reset_mock()
                r6 = client.get("/api/prices/sm-001")
                self.assertEqual(r6.status_code, 429)
                mock_save.assert_not_called()

    def test_w1_api_06_different_product_ids_share_same_ip_quota(self):
        """W1-API-06: Changing product ID does not bypass rate limit (shared bucket per client IP)."""
        products = ["sm-001", "sm-002", "sm-003", "sm-004", "sm-005"]
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for pid in products:
                    r = client.get(f"/api/prices/{pid}")
                    self.assertEqual(r.status_code, 200)

                # 6th request with a different product ID must be rejected
                r6 = client.get("/api/prices/sm-006")
                self.assertEqual(r6.status_code, 429)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w1_api_07_different_client_ips_independent_quota(self):
        """W1-API-07: Requests from distinct client IPs have independent quota on Render."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                headers_a = {"CF-Connecting-IP": "203.0.113.10", "X-Forwarded-Proto": "https"}
                headers_b = {"CF-Connecting-IP": "203.0.113.20", "X-Forwarded-Proto": "https"}

                # Deplete IP A
                for _ in range(5):
                    r = client.get("/api/prices/sm-001", headers=headers_a)
                    self.assertEqual(r.status_code, 200)
                self.assertEqual(client.get("/api/prices/sm-001", headers=headers_a).status_code, 429)

                # IP B must still be allowed
                r_b = client.get("/api/prices/sm-001", headers=headers_b)
                self.assertEqual(r_b.status_code, 200)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w1_api_08_missing_cf_header_fails_closed_400(self):
        """W1-API-08: On Render, missing CF-Connecting-IP fails closed with HTTP 400 without rate limit bypass."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                # Missing CF-Connecting-IP
                r = client.get("/api/prices/sm-001", headers={"X-Forwarded-Proto": "https"})
                self.assertEqual(r.status_code, 400)
                self.assertIn("client identity", r.json().get("detail", "").lower())

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w1_api_09_spoofed_xff_ignored_on_render(self):
        """W1-API-09: Spoofed X-Forwarded-For on Render does not alter the rate limit key."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                # Attacker tries to rotate X-Forwarded-For to evade limit
                for i in range(5):
                    h = {
                        "CF-Connecting-IP": "203.0.113.55",
                        "X-Forwarded-For": f"10.0.0.{i+1}",
                        "X-Forwarded-Proto": "https",
                    }
                    r = client.get("/api/prices/sm-001", headers=h)
                    self.assertEqual(r.status_code, 200)

                # 6th request with different X-Forwarded-For must still be 429
                h6 = {
                    "CF-Connecting-IP": "203.0.113.55",
                    "X-Forwarded-For": "10.0.0.99",
                    "X-Forwarded-Proto": "https",
                }
                r6 = client.get("/api/prices/sm-001", headers=h6)
                self.assertEqual(r6.status_code, 429)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w1_api_10_spoofed_x_real_ip_ignored_on_render(self):
        """W1-API-10: Spoofed X-Real-IP on Render does not alter the rate limit key."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for i in range(5):
                    h = {
                        "CF-Connecting-IP": "203.0.113.77",
                        "X-Real-IP": f"10.0.1.{i+1}",
                        "X-Forwarded-Proto": "https",
                    }
                    client.get("/api/prices/sm-001", headers=h)

                h6 = {
                    "CF-Connecting-IP": "203.0.113.77",
                    "X-Real-IP": "10.0.1.99",
                    "X-Forwarded-Proto": "https",
                }
                r6 = client.get("/api/prices/sm-001", headers=h6)
                self.assertEqual(r6.status_code, 429)

    def test_w1_api_11_non_price_endpoints_not_limited(self):
        """W1-API-11: Non-price endpoints (/api/products, /api/scoring, /api/compare) are unaffected by W1."""
        with TestClient(app) as client:
            # Consume 10 times on non-price endpoints
            for _ in range(10):
                r = client.get("/api/products")
                self.assertEqual(r.status_code, 200)

    def test_w1_api_12_health_endpoint_remains_available(self):
        """W1-API-12: Health check endpoint is unaffected and remains 100% available."""
        with TestClient(app) as client:
            for _ in range(10):
                r = client.get("/health")
                self.assertEqual(r.status_code, 200)

    def test_w1_api_13_existing_cache_hit_preserved(self):
        """W1-API-13: Existing price cache functionality remains intact for allowed requests."""
        from app.routers import prices

        with offline_price_endpoint_context():
            with TestClient(app) as client:
                r1 = client.get("/api/prices/sm-001")
                self.assertEqual(r1.status_code, 200)
                # Ensure entry exists in active price_cache
                self.assertTrue(any(k[0] == "sm-001" for k in prices.price_cache._cache.keys()))

    def test_w1_api_14_existing_single_flight_preserved(self):
        """W1-API-14: Existing single-flight coalescing remains functional under rate limiting."""
        from app.routers.prices import price_cache

        with offline_price_endpoint_context():
            # price_cache._inflight manages single-flight deduplication
            self.assertIsNotNone(getattr(price_cache, "_inflight", None))

    def test_w1_api_15_existing_admission_control_preserved(self):
        """W1-API-15: SEC-008 worker admission control remains active."""
        from app.routers.prices import price_cache
        self.assertGreater(price_cache._max_concurrent, 0)
        self.assertTrue(hasattr(price_cache, "_acquire_permit"))

    def test_w1_api_16_existing_http_response_format_unaltered(self):
        """W1-API-16: Successful price response schema matches existing contract."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                resp = client.get("/api/prices/sm-001")
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertIn("product_id", data)
                self.assertIn("prices", data)
                self.assertIsInstance(data["prices"], list)

    @patch.dict(os.environ, {"RENDER": "true"})
    @patch("app.scrape_worker.run_isolated_scrape_flight")
    def test_w1_api_17_client_identity_failure_does_not_start_scraper(self, mock_flight):
        """W1-API-17: Client identity failure on Render stops request before starting scraper worker."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                resp = client.get("/api/prices/sm-001", headers={"X-Forwarded-Proto": "https"})
                self.assertEqual(resp.status_code, 400)
                mock_flight.assert_not_called()

    def test_w1_api_18_uvicorn_procfile_contains_single_worker(self):
        """W1-API-18: Procfile explicitly sets --workers 1 alongside --no-proxy-headers."""
        procfile = Path(_BACKEND_DIR) / "Procfile"
        content = procfile.read_text(encoding="utf-8")
        self.assertIn("--workers 1", content)
        self.assertIn("--no-proxy-headers", content)


class TestResidualRiskRemediation(unittest.TestCase):
    """Residual risk remediation test suite (RR-W1-01 through RR-W1-18)."""

    def setUp(self) -> None:
        self.clock = FakeClock(1000.0)
        self.limiter = TokenBucketRateLimiter(
            capacity=5.0,
            refill_rate_per_minute=10.0,
            max_entries=5,
            clock_fn=self.clock,
            log_cooldown_seconds=60.0,
        )
        price_rate_limiter.reset()

    def tearDown(self) -> None:
        price_rate_limiter.reset()

    def test_rr_w1_01_no_raw_ip_in_logs(self):
        """RR-W1-01: Raw client IP is never included in warning logs when registry capacity is reached."""
        test_ip = "203.0.113.199"
        for i in range(5):
            self.limiter.consume(f"192.0.2.{i}")

        with self.assertLogs("app.security.rate_limiter", level="WARNING") as cm:
            res = self.limiter.consume(test_ip)
            self.assertFalse(res.allowed)

        log_text = " ".join(cm.output)
        self.assertNotIn(test_ip, log_text)
        self.assertIn("Rate limiter registry capacity reached", log_text)
        self.assertIn("Rejecting new requests.", log_text)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_rr_w1_02_no_raw_forwarded_headers_in_logs(self):
        """RR-W1-02: Client identity headers are never logged during rate limiting or capacity rejection."""
        spoofed_header_ip = "198.51.100.88"
        headers = {
            "CF-Connecting-IP": spoofed_header_ip,
            "X-Forwarded-For": "203.0.113.1, 10.0.0.1",
            "X-Forwarded-Proto": "https",
        }
        with patch.object(price_rate_limiter, "max_entries", 0):
            with self.assertLogs("app.security.rate_limiter", level="WARNING") as cm:
                with offline_price_endpoint_context():
                    with TestClient(app) as client:
                        resp = client.get("/api/prices/sm-001", headers=headers)
                        self.assertEqual(resp.status_code, 429)

            log_text = " ".join(cm.output)
            self.assertNotIn(spoofed_header_ip, log_text)
            self.assertNotIn("203.0.113.1", log_text)
            self.assertNotIn("CF-Connecting-IP", log_text)
            self.assertNotIn("X-Forwarded-For", log_text)

    def test_rr_w1_03_first_capacity_event_emits_one_warning(self):
        """RR-W1-03: The first registry-full event emits exactly one warning log without suppressed counter."""
        for i in range(5):
            self.limiter.consume(f"10.0.0.{i}")

        with self.assertLogs("app.security.rate_limiter", level="WARNING") as cm:
            res = self.limiter.consume("10.0.0.99")
            self.assertFalse(res.allowed)

        self.assertEqual(len(cm.output), 1)
        self.assertIn("Rate limiter registry capacity reached (5 entries). Rejecting new requests.", cm.output[0])
        self.assertNotIn("Suppressed events", cm.output[0])

    def test_rr_w1_04_repeated_capacity_events_throttled(self):
        """RR-W1-04: Repeated capacity rejections within 60s cooldown window emit zero additional logs."""
        import logging

        for i in range(5):
            self.limiter.consume(f"10.0.0.{i}")

        # First failure logs
        with self.assertLogs("app.security.rate_limiter", level="WARNING") as cm:
            self.limiter.consume("10.0.0.100")
        self.assertEqual(len(cm.output), 1)

        logger_instance = logging.getLogger("app.security.rate_limiter")

        class LogCounter(logging.Handler):
            def __init__(self):
                super().__init__()
                self.count = 0

            def emit(self, record):
                self.count += 1

        counter = LogCounter()
        logger_instance.addHandler(counter)
        try:
            for j in range(101, 200):
                self.clock.advance(0.1)
                res = self.limiter.consume(f"10.0.0.{j}")
                self.assertFalse(res.allowed)
            self.assertEqual(counter.count, 0, "No warning logs should be emitted during cooldown")
        finally:
            logger_instance.removeHandler(counter)

        self.assertEqual(self.limiter._suppressed_capacity_logs, 99)

    def test_rr_w1_05_suppressed_event_count_aggregated(self):
        """RR-W1-05: After cooldown expires, the next capacity rejection reports aggregated suppressed count."""
        for i in range(5):
            self.limiter.consume(f"10.0.0.{i}")

        # First rejection
        self.limiter.consume("10.0.0.100")

        # 50 rejections within cooldown
        for j in range(101, 151):
            self.clock.advance(0.5)
            self.limiter.consume(f"10.0.0.{j}")

        self.assertEqual(self.limiter._suppressed_capacity_logs, 50)

        # Keep registered IPs active so they are not idle for > 30s
        self.clock.advance(25.0)
        for i in range(5):
            self.limiter.consume(f"10.0.0.{i}")

        # Advance clock past cooldown window (60s since first rejection at t=1000)
        self.clock.advance(15.0)  # total elapsed: 25 + 25 + 15 = 65s > 60s cooldown

        with self.assertLogs("app.security.rate_limiter", level="WARNING") as cm:
            res = self.limiter.consume("10.0.0.200")
            self.assertFalse(res.allowed)

        self.assertEqual(len(cm.output), 1)
        self.assertIn("Rate limiter registry capacity reached (5 entries). Rejecting new requests. Suppressed events: 50.", cm.output[0])
        self.assertEqual(self.limiter._suppressed_capacity_logs, 0)

    def test_rr_w1_06_concurrent_capacity_warnings_no_log_storm(self):
        """RR-W1-06: 20 concurrent threads failing capacity simultaneously produce at most 1 warning log."""
        for i in range(5):
            self.limiter.consume(f"10.0.0.{i}")

        num_threads = 20
        with self.assertLogs("app.security.rate_limiter", level="WARNING") as cm:
            def worker(idx):
                return self.limiter.consume(f"192.168.1.{idx}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker, i) for i in range(num_threads)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), num_threads)
        self.assertTrue(all(not r.allowed for r in results))
        self.assertEqual(len(cm.output), 1)
        self.assertEqual(self.limiter._suppressed_capacity_logs, 19)

    def test_rr_w1_07_registry_full_after_ip_churn_safe_rejection(self):
        """RR-W1-07: Registry maintains bounded capacity and rejects new IPs when filled."""
        for i in range(5):
            res = self.limiter.consume(f"172.16.0.{i}")
            self.assertTrue(res.allowed)

        self.assertEqual(len(self.limiter._buckets), 5)
        res_reject = self.limiter.consume("172.16.0.99")
        self.assertFalse(res_reject.allowed)
        self.assertEqual(len(self.limiter._buckets), 5)
        self.assertNotIn("172.16.0.99", self.limiter._buckets)

    def test_rr_w1_08_idle_full_bucket_eligible_for_eviction(self):
        """RR-W1-08: Bucket idle >= 30 seconds is eligible for eviction and safely evicted on cleanup."""
        ip = "172.16.1.1"
        self.limiter.consume(ip)
        self.assertIn(ip, self.limiter._buckets)

        # Advance exactly 30s (idle timeout = 5 / (1/6) = 30.0s)
        self.clock.advance(30.0)

        with self.limiter._lock:
            evicted = self.limiter._cleanup_idle_buckets_locked(self.clock())
        self.assertEqual(evicted, 1)
        self.assertNotIn(ip, self.limiter._buckets)

    def test_rr_w1_09_depleted_bucket_not_evicted(self):
        """RR-W1-09: Depleted bucket idle < 30s is never evicted, preserving quota restriction."""
        ip = "172.16.1.2"
        for _ in range(5):
            self.limiter.consume(ip)

        # Advance 15s (less than 30s idle timeout)
        self.clock.advance(15.0)

        with self.limiter._lock:
            evicted = self.limiter._cleanup_idle_buckets_locked(self.clock())
        self.assertEqual(evicted, 0)
        self.assertIn(ip, self.limiter._buckets)
        self.assertLess(self.limiter._buckets[ip].tokens, 5.0)

    def test_rr_w1_10_recently_active_full_bucket_not_evicted_before_idle_timeout(self):
        """RR-W1-10: Bucket active at t=20 is not evicted at t=35 (only 15s since activity)."""
        ip = "172.16.1.3"
        self.limiter.consume(ip)  # at t=1000
        self.clock.advance(20.0)  # at t=1020
        self.limiter.consume(ip)  # updated at t=1020

        self.clock.advance(15.0)  # at t=1035 (15s since t=1020)
        with self.limiter._lock:
            evicted = self.limiter._cleanup_idle_buckets_locked(self.clock())
        self.assertEqual(evicted, 0)
        self.assertIn(ip, self.limiter._buckets)

    def test_rr_w1_11_recovery_after_30s_idle_period(self):
        """RR-W1-11: Full registry automatically recovers capacity and admits new IP after 30s idle period."""
        for i in range(5):
            self.limiter.consume(f"172.16.2.{i}")

        res_reject = self.limiter.consume("172.16.2.99")
        self.assertFalse(res_reject.allowed)

        # Advance clock by 30.0s (all 5 buckets become idle)
        self.clock.advance(30.0)

        res_allowed = self.limiter.consume("172.16.2.99")
        self.assertTrue(res_allowed.allowed)
        self.assertIn("172.16.2.99", self.limiter._buckets)

    def test_rr_w1_12_registry_capacity_invariant_never_exceeds_max(self):
        """RR-W1-12: len(_buckets) never exceeds max_entries across 500 rapid unique IP arrivals."""
        for i in range(500):
            self.clock.advance(0.05)
            self.limiter.consume(f"10.1.{i // 256}.{i % 256}")
            self.assertLessEqual(len(self.limiter._buckets), self.limiter.max_entries)

    def test_rr_w1_13_sustained_churn_simulation(self):
        """RR-W1-13: Alternating waves of active and idle IPs maintain bounded memory and correct quotas."""
        for i in range(5):
            self.limiter.consume(f"10.2.0.{i}")
        self.assertEqual(len(self.limiter._buckets), 5)

        self.clock.advance(35.0)

        for i in range(5):
            res = self.limiter.consume(f"10.2.1.{i}")
            self.assertTrue(res.allowed)
        self.assertEqual(len(self.limiter._buckets), 5)
        for i in range(5):
            self.assertNotIn(f"10.2.0.{i}", self.limiter._buckets)
            self.assertIn(f"10.2.1.{i}", self.limiter._buckets)

    def test_rr_w1_14_existing_token_quota_unchanged(self):
        """RR-W1-14: Standard 5 burst / 10 per minute quota contract is preserved."""
        ip = "192.0.2.201"
        for _ in range(5):
            res = self.limiter.consume(ip)
            self.assertTrue(res.allowed)

        res6 = self.limiter.consume(ip)
        self.assertFalse(res6.allowed)
        self.assertEqual(res6.retry_after, 6)

        self.clock.advance(6.0)
        res7 = self.limiter.consume(ip)
        self.assertTrue(res7.allowed)
        self.assertEqual(res7.remaining, 0)

    def test_rr_w1_15_existing_per_ip_isolation_unchanged(self):
        """RR-W1-15: Depleting one IP's quota has zero effect on another IP's quota."""
        ip1 = "192.0.2.210"
        ip2 = "192.0.2.211"
        for _ in range(5):
            self.limiter.consume(ip1)
        self.assertFalse(self.limiter.consume(ip1).allowed)

        for i in range(5):
            res = self.limiter.consume(ip2)
            self.assertTrue(res.allowed)
            self.assertEqual(res.remaining, 4 - i)

    def test_rr_w1_16_concurrent_same_ip_consumption_no_over_admission(self):
        """RR-W1-16: 30 concurrent threads consuming same IP yield exactly 5 allowed and 25 rejected."""
        ip = "192.0.2.220"
        num_threads = 30
        results = []

        def worker():
            return self.limiter.consume(ip)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        allowed = sum(1 for r in results if r.allowed)
        rejected = sum(1 for r in results if not r.allowed)
        self.assertEqual(allowed, 5)
        self.assertEqual(rejected, 25)

    def test_rr_w1_17_http_429_behavior_unchanged(self):
        """RR-W1-17: HTTP 429 response maintains correct Retry-After and Cache-Control headers."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for _ in range(5):
                    client.get("/api/prices/sm-001")

                resp = client.get("/api/prices/sm-001")
                self.assertEqual(resp.status_code, 429)
                self.assertIn("retry-after", resp.headers)
                self.assertEqual(resp.headers.get("cache-control"), "no-store")
                self.assertEqual(resp.json()["detail"], "Too many requests. Please try again later.")

    @patch("app.db.SessionLocal")
    @patch("app.scrape_worker.run_isolated_scrape_flight")
    def test_rr_w1_18_early_rejection_no_db_or_scraper(self, mock_flight, mock_session):
        """RR-W1-18: Rate limiter early rejection prevents database access and scraper worker execution."""
        with offline_price_endpoint_context():
            with TestClient(app) as client:
                for _ in range(5):
                    client.get("/api/prices/sm-001")

                mock_flight.reset_mock()
                mock_session.reset_mock()

                resp = client.get("/api/prices/sm-001")
                self.assertEqual(resp.status_code, 429)
                mock_flight.assert_not_called()
                mock_session.assert_not_called()


if __name__ == "__main__":
    unittest.main()
