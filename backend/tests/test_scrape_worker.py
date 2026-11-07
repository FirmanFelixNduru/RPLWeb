"""SEC-008 AC-08: Real Windows/POSIX `spawn` process-isolation, IPC, and deadline tests.

Covers T-01, T-02, T-03 (including real 35s wall-clock deadline acceptance),
T-06, T-07, T-08 (process cancellation & reap), T-09 (late result at cutoff),
T-13 (multi-product concurrent flights), and T-16 (pre-spawn/startup overhead
inside single shared budget).

Note on T-05: Cooperative parser-checkpoint cancellation was NOT selected under
approved Decision D9 (Process Isolation). T-05 is therefore NOT APPLICABLE and
is intentionally not claimed as passed.
"""
from __future__ import annotations

import asyncio
import ctypes
import importlib
import importlib.util
import json
import multiprocessing
import os
import signal
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

_BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from tests._db_guard import enforce_safe_test_db_env

enforce_safe_test_db_env()

import httpx


# ──────────────────────────────────────────────────────────────────────
# Cross-platform OS-level process liveness check (no external deps)
# ──────────────────────────────────────────────────────────────────────
def is_os_pid_running(pid: int | None) -> bool:
    """Return True if an OS process with `pid` is still actively running."""
    if not pid or pid <= 0:
        return False
    if os.name == "nt":
        SYNCHRONIZE = 0x00100000
        WAIT_TIMEOUT = 0x00000102
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
        if not handle:
            return False
        try:
            res = kernel32.WaitForSingleObject(handle, 0)
            return res == WAIT_TIMEOUT
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


# ──────────────────────────────────────────────────────────────────────
# Top-level deterministic `spawn`-safe worker fixtures (zero closures)
# ──────────────────────────────────────────────────────────────────────
def _all_three_succeed_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        host = (request.url.host or "").lower()
        if "tokopedia.com" in host:
            html = (
                '<div data-testid="spnSRPProdName">Samsung Galaxy S24 Ultra 256GB</div>'
                '<span data-testid="spnSRPProdPrice">Rp 19.499.000</span>'
            )
            return httpx.Response(200, text=html)
        if "shopee.co.id" in host:
            html = (
                '<div class="shopee-search-item-result__item-name">Samsung Galaxy S24 Ultra</div>'
                '<div class="shopee-price">Rp 19.199.000</div>'
            )
            return httpx.Response(200, text=html)
        if "lazada.co.id" in host:
            html = (
                '<div class="title--wFj93">Samsung Galaxy S24 Ultra Official</div>'
                '<div class="price--NVB62">Rp 19.599.000</div>'
            )
            return httpx.Response(200, text=html)
        return httpx.Response(404, text="unknown")

    return httpx.MockTransport(handler)


def worker_t01_three_marketplaces_ok(product_id: str, product_name: str) -> list[dict]:
    """Runs production `scrape_marketplaces_worker` with offline MockTransport and audits child isolation."""
    # Verify inside the child process that DB modules and DB env vars are absent.
    if "app.db" in sys.modules or "sqlalchemy" in sys.modules or "psycopg2" in sys.modules:
        raise RuntimeError("DB module leaked into child worker process")
    if "DATABASE_URL" in os.environ or "TEST_DATABASE_URL" in os.environ:
        raise RuntimeError("Database credentials leaked into child worker environment")

    from app.scrape_worker import scrape_marketplaces_worker

    offers = scrape_marketplaces_worker(
        product_id,
        product_name,
        transport_factory=_all_three_succeed_transport,
    )
    # Re-verify after running full httpx + BeautifulSoup scrape stack.
    if "app.db" in sys.modules or "sqlalchemy" in sys.modules:
        raise RuntimeError("DB module imported during scrape_marketplaces_worker")
    return offers


def worker_t02_one_timeout_two_succeed(product_id: str, product_name: str) -> list[dict]:
    """Shopee raises ReadTimeout individually while Tokopedia and Lazada succeed within budget."""
    closed_flags: list[bool] = []

    class TrackingMockTransport(httpx.AsyncBaseTransport):
        def __init__(self) -> None:
            self.idx = len(closed_flags)
            closed_flags.append(False)

        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            host = (request.url.host or "").lower()
            if "shopee.co.id" in host:
                raise httpx.ReadTimeout("simulated individual marketplace read timeout")
            if "tokopedia.com" in host:
                return httpx.Response(
                    200,
                    text=(
                        f'<div data-testid="spnSRPProdName">{product_name}</div>'
                        '<span data-testid="spnSRPProdPrice">Rp 19.399.000</span>'
                    ),
                )
            return httpx.Response(
                200,
                text=(
                    f'<div class="title--wFj93">{product_name}</div>'
                    '<div class="price--NVB62">Rp 19.699.000</div>'
                ),
            )

        async def aclose(self) -> None:
            closed_flags[self.idx] = True

    from app.scrape_worker import scrape_marketplaces_worker

    offers = scrape_marketplaces_worker(
        product_id,
        product_name,
        transport_factory=TrackingMockTransport,
    )
    if len(closed_flags) != 3 or not all(closed_flags):
        raise RuntimeError(f"Expected 3 closed HTTP transports in worker, got {closed_flags}")
    return offers


def worker_hang_sleep(product_id: str, product_name: str) -> list[dict]:
    """Simulates slow/stalled HTTP fetch exceeding total flight budget."""
    if product_name and os.path.exists(product_name):
        Path(product_name).write_text(str(os.getpid()), encoding="utf-8")
    time.sleep(120.0)
    return []


def worker_t06_cpu_hang_ignore_sigterm(product_id: str, product_name: str) -> list[dict]:
    """Ignores SIGTERM (where supported) and spins in an uninterruptible Python CPU loop."""
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    except Exception:
        pass
    if product_name and os.path.exists(product_name):
        Path(product_name).write_text(str(os.getpid()), encoding="utf-8")
    acc = 0
    while True:
        acc = (acc + 1) & 0xFFFFFF


def worker_t07_hard_crash_exit2(product_id: str, product_name: str) -> list[dict]:
    """Terminates abruptly via os._exit(2) before writing any IPC bytes."""
    os._exit(2)


def worker_t07_unhandled_exception(product_id: str, product_name: str) -> list[dict]:
    """Raises an unhandled exception inside worker target."""
    raise ValueError("simulated parser crash")


def raw_entry_truncated_ipc(send_conn, worker_fn, product_id: str, product_name: str) -> None:
    """Custom raw entry writing truncated JSON bytes and exiting 0 to test parent frame validation."""
    try:
        send_conn.send_bytes(b'{"status": "ok", "offers": [{"marketplace": "Tokopedia"')
    finally:
        send_conn.close()


def worker_t07_spoofed_domain_payload(product_id: str, product_name: str) -> list[dict]:
    """Returns structurally valid JSON with a spoofed non-official marketplace URL."""
    return [
        {
            "marketplace": "Tokopedia",
            "price": 19_000_000,
            "url": "https://evil-tokopedia.com/phish",
            "seller": "Attacker",
            "available": True,
            "captured_at": "2026-11-07T00:00:00+00:00",
        }
    ]


def worker_t07_out_of_bounds_price_payload(product_id: str, product_name: str) -> list[dict]:
    """Returns JSON with Rp 100 mock price violating [50_000, 150_000_000] bounds."""
    return [
        {
            "marketplace": "Tokopedia",
            "price": 100,
            "url": "https://www.tokopedia.com/search?q=s24",
            "seller": "Mock",
            "available": True,
            "captured_at": "2026-11-07T00:00:00+00:00",
        }
    ]


def raw_entry_send_valid_then_hang_past_cutoff(
    send_conn, worker_fn, product_id: str, product_name: str
) -> None:
    """Writes valid JSON right near cutoff and refuses to exit so worker misses deadline (T-09)."""
    try:
        time.sleep(0.95)
        payload = {
            "status": "ok",
            "offers": [
                {
                    "marketplace": "Tokopedia",
                    "price": 18_888_000,
                    "url": "https://www.tokopedia.com/search?q=sm-001",
                    "seller": "Late Seller",
                    "available": True,
                    "captured_at": "2026-11-07T00:00:00+00:00",
                }
            ],
        }
        send_conn.send_bytes(json.dumps(payload).encode("utf-8"))
        time.sleep(30.0)
    except Exception:
        pass
    finally:
        try:
            send_conn.close()
        except Exception:
            pass


def worker_t13_keyed_fast_or_slow(product_id: str, product_name: str) -> list[dict]:
    """Product-specific deterministic worker: lp-001 hangs while sm-001 returns valid offer."""
    if product_id == "lp-001":
        time.sleep(30.0)
        return []
    price = 19_111_000 if product_id == "sm-001" else 17_222_000
    return [
        {
            "marketplace": "Tokopedia",
            "price": price,
            "url": f"https://www.tokopedia.com/search?q={product_id}",
            "seller": f"Seller {product_name}",
            "available": True,
            "captured_at": "2026-11-07T00:00:00+00:00",
        }
    ]


def worker_t16_slow_after_startup(product_id: str, product_name: str) -> list[dict]:
    """Sleeps 0.9s after spawn; passes a fresh 1.6s budget alone, fails if 0.65s pre-spawn consumed budget."""
    time.sleep(0.9)
    return [
        {
            "marketplace": "Tokopedia",
            "price": 19_000_000,
            "url": "https://www.tokopedia.com/search?q=s24",
            "seller": "Tokopedia Seller",
            "available": True,
            "captured_at": "2026-11-07T00:00:00+00:00",
        }
    ]


# ──────────────────────────────────────────────────────────────────────
# Process Isolation Test Suite
# ──────────────────────────────────────────────────────────────────────
class TestScrapeWorkerLifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        spec = importlib.util.find_spec("app.scrape_worker")
        self.assertIsNotNone(
            spec,
            "SEC-008 AC-08 process isolation worker module app.scrape_worker is missing",
        )
        self.sw = importlib.import_module("app.scrape_worker")
        self.ps = importlib.import_module("app.price_service")
        self.scraper = importlib.import_module("app.scraper")

    def tearDown(self) -> None:
        if hasattr(self.sw, "active_worker_pids"):
            self.assertEqual(
                self.sw.active_worker_pids(),
                [],
                "No residual subprocess worker PIDs may remain after test",
            )
        self.assertEqual(
            multiprocessing.active_children(),
            [],
            "No residual worker child processes may remain after test",
        )

    async def test_t01_normal_three_marketplaces_flight_end_to_end(self) -> None:
        """T-01: 3 marketplaces succeed in child -> sorted, persisted once in parent, cached 300s/deep-copy."""
        cache = self.ps.PriceCache(worker_fn=worker_t01_three_marketplaces_ok)
        # Temporarily set dummy DB env vars in parent to prove child scrubs them cleanly.
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://u:secret@localhost:5432/comparebuy_test",
                "TEST_DATABASE_URL": "postgresql://u:secret@localhost:5432/comparebuy_test",
            },
        ), patch("app.repositories.price_repo.save_price_snapshot", return_value=True) as save_mock:
            t0 = time.monotonic()
            first = await cache.get("sm-001", "Samsung Galaxy S24 Ultra")
            elapsed = time.monotonic() - t0

            self.assertLess(elapsed, 35.0)
            self.assertEqual([p.price for p in first.prices], [19_199_000, 19_499_000, 19_599_000])
            self.assertTrue(all(p.source == "scraped" for p in first.prices))
            self.assertEqual(save_mock.call_count, 3)

            # Deep copy & cache hit verification (0 new workers or saves on hit)
            first.prices[0].price = 1
            first.prices.clear()
            second = await cache.get("sm-001", "Samsung Galaxy S24 Ultra")
            self.assertEqual([p.price for p in second.prices], [19_199_000, 19_499_000, 19_599_000])
            self.assertEqual(save_mock.call_count, 3)
            self.assertFalse(cache._inflight)

    async def test_t02_individual_marketplace_timeout_preserves_others_and_merges_fallback(self) -> None:
        """T-02: 1 marketplace times out individually, 2 succeed -> fallback merged for 1, clients closed."""
        cache = self.ps.PriceCache(worker_fn=worker_t02_one_timeout_two_succeed)
        with patch("app.repositories.price_repo.save_price_snapshot", return_value=True) as save_mock:
            result = await cache.get("sm-001", "Samsung Galaxy S24 Ultra")

        by_mp = {p.marketplace: p for p in result.prices}
        self.assertEqual(by_mp["Tokopedia"].source, "scraped")
        self.assertEqual(by_mp["Tokopedia"].price, 19_399_000)
        self.assertEqual(by_mp["Lazada"].source, "scraped")
        self.assertEqual(by_mp["Lazada"].price, 19_699_000)
        self.assertEqual(by_mp["Shopee"].source, "fallback")
        self.assertIsNone(by_mp["Shopee"].captured_at)
        self.assertIn("Acuan Simulasi:", by_mp["Shopee"].target_configuration or "")
        self.assertEqual([p.price for p in result.prices], sorted(p.price for p in result.prices))
        self.assertEqual(save_mock.call_count, 3)

    async def test_t03_total_budget_exceeded_stops_worker_no_cache_no_persistence(self) -> None:
        """T-03: Hanging worker hits budget -> single terminal timeout for all waiters, 0 cache, 0 DB write."""
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            pid_file = tf.name
        try:
            cache = self.ps.PriceCache(worker_fn=worker_hang_sleep)
            with patch.object(self.scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", 1.8), patch(
                "app.repositories.price_repo.save_price_snapshot", return_value=True
            ) as save_mock:
                t0 = time.monotonic()
                outcomes = await asyncio.gather(
                    *(cache.get("sm-001", pid_file) for _ in range(4)),
                    return_exceptions=True,
                )
                elapsed = time.monotonic() - t0

            self.assertLessEqual(elapsed, 1.85)
            for err in outcomes:
                self.assertIsInstance(err, self.sw.ScrapeTimeoutError)
                self.assertTrue(err.worker_stopped)
                self.assertTrue(err.reaped)
                self.assertTrue(err.within_budget)
            # Confirm all 4 waiters shared the exact same worker PID and it is dead at OS level
            pids = {err.worker_pid for err in outcomes}
            self.assertEqual(len(pids), 1)
            worker_pid = next(iter(pids))
            self.assertIsNotNone(worker_pid)
            self.assertFalse(is_os_pid_running(worker_pid))
            self.assertFalse(cache._cache)
            self.assertFalse(cache._inflight)
            save_mock.assert_not_called()
        finally:
            Path(pid_file).unlink(missing_ok=True)

    async def test_t03_real_35s_wall_clock_deadline_enforcement(self) -> None:
        """T-03 (35s acceptance): Real 35.0s default budget starts before spawn and reaps worker <= 35.0s."""
        self.assertEqual(self.scraper.TOTAL_SCRAPE_TIMEOUT_SECONDS, 35.0)
        t0 = time.monotonic()
        with self.assertRaises(self.sw.ScrapeTimeoutError) as ctx:
            await self.sw.run_isolated_scrape_flight(
                "sm-001",
                "Samsung Galaxy S24 Ultra",
                budget_seconds=self.scraper.TOTAL_SCRAPE_TIMEOUT_SECONDS,
                worker_fn=worker_hang_sleep,
            )
        wall_elapsed = time.monotonic() - t0
        err = ctx.exception
        self.assertTrue(err.worker_stopped)
        self.assertTrue(err.reaped)
        self.assertTrue(err.within_budget)
        self.assertLessEqual(err.elapsed, 35.0)
        self.assertLessEqual(wall_elapsed, 35.05)
        # Ensure cleanup did NOT happen prematurely (must run past 32.5s before 2.0s cleanup reserve)
        self.assertGreaterEqual(err.elapsed, 32.5)
        self.assertFalse(is_os_pid_running(err.worker_pid))

    async def test_t06_cpu_bound_hang_ignoring_sigterm_is_killed_and_reaped_within_budget(self) -> None:
        """T-06: Child spinning CPU & ignoring SIGTERM is forcibly killed and reaped before budget D."""
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            pid_file = tf.name
        try:
            budget = 1.8
            t0 = time.monotonic()
            with self.assertRaises(self.sw.ScrapeTimeoutError) as ctx:
                await self.sw.run_isolated_scrape_flight(
                    "sm-001",
                    pid_file,
                    budget_seconds=budget,
                    worker_fn=worker_t06_cpu_hang_ignore_sigterm,
                )
            elapsed = time.monotonic() - t0
            err = ctx.exception
            self.assertTrue(err.worker_stopped)
            self.assertTrue(err.reaped)
            self.assertTrue(err.within_budget)
            self.assertIsNotNone(err.exitcode)
            self.assertNotEqual(err.exitcode, 0)
            self.assertLessEqual(err.elapsed, budget)
            self.assertLessEqual(elapsed, budget + 0.05)
            recorded_pid_txt = Path(pid_file).read_text(encoding="utf-8").strip()
            if recorded_pid_txt:
                self.assertEqual(int(recorded_pid_txt), err.worker_pid)
            self.assertFalse(is_os_pid_running(err.worker_pid))
        finally:
            Path(pid_file).unlink(missing_ok=True)

    async def test_t07_worker_crash_truncated_and_invalid_ipc_payloads_rejected_and_recover(self) -> None:
        """T-07: Hard crash, unhandled error, truncated JSON, spoofed URL, and bad price all fail closed."""
        with patch("app.repositories.price_repo.save_price_snapshot", return_value=True) as save_mock:
            # 1) Hard os._exit(2) before IPC message
            cache_crash = self.ps.PriceCache(worker_fn=worker_t07_hard_crash_exit2)
            with self.assertRaises(self.sw.ScrapeWorkerError):
                await cache_crash.get("sm-001", "Phone")
            self.assertFalse(cache_crash._cache)
            self.assertFalse(cache_crash._inflight)

            # 2) Unhandled ValueError in child
            cache_exc = self.ps.PriceCache(worker_fn=worker_t07_unhandled_exception)
            with self.assertRaises(self.sw.ScrapeWorkerError):
                await cache_exc.get("sm-001", "Phone")
            self.assertFalse(cache_exc._cache)

            # 3) Truncated IPC bytes despite exitcode 0
            with self.assertRaises(self.sw.ScrapeWorkerError):
                await self.sw.run_isolated_scrape_flight(
                    "sm-001",
                    "Phone",
                    budget_seconds=3.0,
                    worker_fn=worker_t01_three_marketplaces_ok,
                    _entry_override=raw_entry_truncated_ipc,
                )

            # 4) Spoofed URL & out-of-bounds Rp 100 price rejected by parent validator
            for bad_worker in (worker_t07_spoofed_domain_payload, worker_t07_out_of_bounds_price_payload):
                cache_bad = self.ps.PriceCache(worker_fn=bad_worker)
                with self.assertRaises(self.sw.ScrapeWorkerError):
                    await cache_bad.get("sm-001", "Phone")
                self.assertFalse(cache_bad._cache)

            save_mock.assert_not_called()

            # 5) Recovery: next request on same cache instance after crash succeeds cleanly
            cache_crash._worker_fn = worker_t01_three_marketplaces_ok
            recovered = await cache_crash.get("sm-001", "Samsung Galaxy S24 Ultra")
            self.assertEqual(len(recovered.prices), 3)
            self.assertEqual(save_mock.call_count, 3)

    async def test_t08_process_waiter_shielding_and_last_waiter_repeated_cancel_reaps_worker(self) -> None:
        """T-08 (process boundary): 1st waiter cancel spares worker; last waiter repeated cancel kills & reaps."""
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            pid_file = tf.name
        try:
            cache = self.ps.PriceCache(worker_fn=worker_hang_sleep)
            with patch("app.repositories.price_repo.save_price_snapshot", return_value=True) as save_mock:
                w1 = asyncio.create_task(cache.get("sm-001", pid_file))
                w2 = asyncio.create_task(cache.get("sm-001", pid_file))

                # Wait until child actually wrote its PID
                deadline = time.monotonic() + 5.0
                child_pid = None
                while time.monotonic() < deadline:
                    txt = Path(pid_file).read_text(encoding="utf-8").strip()
                    if txt:
                        child_pid = int(txt)
                        break
                    await asyncio.sleep(0.02)
                self.assertIsNotNone(child_pid, "Child worker did not start within 5s")
                self.assertTrue(is_os_pid_running(child_pid))

                # Cancel waiter 1 -> worker MUST stay alive for waiter 2
                w1.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await w1
                self.assertTrue(is_os_pid_running(child_pid))

                # Cancel last waiter (w2) repeatedly during teardown -> worker MUST stop & be reaped
                w2.cancel()
                await asyncio.sleep(0)
                w2.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await w2

                self.assertFalse(is_os_pid_running(child_pid))
                self.assertFalse(cache._inflight)
                self.assertFalse(cache._cache)
                save_mock.assert_not_called()
        finally:
            Path(pid_file).unlink(missing_ok=True)

    async def test_t09_late_worker_result_at_cutoff_rejected_without_cache_poisoning(self) -> None:
        """T-09: Valid payload written when worker fails to exit before cutoff is discarded; cache unpoisoned."""
        with self.assertRaises(self.sw.ScrapeTimeoutError) as ctx:
            await self.sw.run_isolated_scrape_flight(
                "sm-001",
                "Samsung Galaxy S24 Ultra",
                budget_seconds=1.2,
                worker_fn=worker_t01_three_marketplaces_ok,
                _entry_override=raw_entry_send_valid_then_hang_past_cutoff,
            )
        self.assertTrue(ctx.exception.worker_stopped)
        self.assertTrue(ctx.exception.reaped)
        self.assertFalse(is_os_pid_running(ctx.exception.worker_pid))

    async def test_t13_concurrent_distinct_products_isolated_flights_and_deadlines(self) -> None:
        """T-13: Distinct product keys execute isolated worker flights and independent deadlines."""
        cache = self.ps.PriceCache(worker_fn=worker_t13_keyed_fast_or_slow)
        with patch.object(self.scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", 3.5), patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=True
        ) as save_mock:
            outcomes = await asyncio.gather(
                cache.get("sm-001", "Alpha"),
                cache.get("sm-002", "Beta"),
                cache.get("lp-001", "SlowLaptop"),
                return_exceptions=True,
            )

        res_sm1, res_sm2, res_lp1 = outcomes
        self.assertEqual(res_sm1.product_id, "sm-001")
        self.assertEqual(res_sm1.product_name, "Alpha")
        self.assertTrue(any(p.price == 19_111_000 and p.seller == "Seller Alpha" for p in res_sm1.prices))

        self.assertEqual(res_sm2.product_id, "sm-002")
        self.assertEqual(res_sm2.product_name, "Beta")
        self.assertTrue(any(p.price == 17_222_000 and p.seller == "Seller Beta" for p in res_sm2.prices))

        self.assertIsInstance(res_lp1, self.sw.ScrapeTimeoutError)
        self.assertIn(("sm-001", "Alpha"), cache._cache)
        self.assertIn(("sm-002", "Beta"), cache._cache)
        self.assertNotIn(("lp-001", "SlowLaptop"), cache._cache)
        self.assertFalse(cache._inflight)
        self.assertEqual(save_mock.call_count, 6)  # 3 offers each for sm-001 and sm-002; 0 for timed-out lp-001

    async def test_t16_slow_pre_spawn_and_startup_consume_single_shared_budget(self) -> None:
        """T-16: Pre-spawn/startup delay consumes the same single monotonic deadline (never resets per stage)."""
        def slow_pre_spawn() -> None:
            time.sleep(0.65)

        t0 = time.monotonic()
        with self.assertRaises(self.sw.ScrapeTimeoutError) as ctx:
            await self.sw.run_isolated_scrape_flight(
                "sm-001",
                "Samsung Galaxy S24 Ultra",
                budget_seconds=1.6,
                worker_fn=worker_t16_slow_after_startup,
                pre_spawn_hook=slow_pre_spawn,
            )
        elapsed = time.monotonic() - t0
        err = ctx.exception
        self.assertTrue(err.worker_stopped)
        self.assertTrue(err.reaped)
        self.assertTrue(err.within_budget)
        self.assertLessEqual(err.elapsed, 1.6)
        self.assertLessEqual(elapsed, 1.65)
        self.assertFalse(is_os_pid_running(err.worker_pid))


def worker_fast_or_hold_by_id(product_id: str, product_name: str) -> list[dict]:
    """Top-level spawn-safe fixture: `slow-*` records PID and blocks; others return valid offer immediately."""
    if product_id.startswith("slow-"):
        if product_name and os.path.isdir(product_name):
            (Path(product_name) / f"{product_id}.pid").write_text(str(os.getpid()), encoding="utf-8")
        time.sleep(30.0)
        return []
    return [
        {
            "marketplace": "Tokopedia",
            "price": 19_250_000,
            "url": f"https://www.tokopedia.com/search?q={product_id}",
            "seller": "Official Store",
            "available": True,
            "captured_at": "2026-11-07T00:00:00+00:00",
        }
    ]


def worker_f05_audit_child_env(product_id: str, product_name: str) -> list[dict]:
    """Verifies child scrubbed DB/secret env vars while leaving normal runtime env intact."""
    forbidden_present = [
        k
        for k in ("DATABASE_URL", "TEST_DATABASE_URL", "JWT_SECRET_KEY", "DB_PASSWORD")
        if k in os.environ
    ]
    if forbidden_present:
        raise RuntimeError(f"Forbidden env keys still visible after _worker_entry scrub: {forbidden_present}")
    return [
        {
            "marketplace": "Tokopedia",
            "price": 19_100_000,
            "url": "https://www.tokopedia.com/search?q=sm-001",
            "seller": "Official Store",
            "available": True,
            "captured_at": "2026-11-07T00:00:00+00:00",
        }
    ]


def worker_rc01_three_marketplaces_profiled(product_id: str, product_name: str) -> list[dict]:
    """Deterministic 3-marketplace fixture worker (0 external network calls) for RC-01."""
    import httpx
    from app.scrape_worker import scrape_marketplaces_worker

    pages = {
        "tokopedia.com": (
            '<html><body><div data-testid="spnSRPProdName">Samsung Galaxy S24 Ultra Resmi</div>'
            '<div data-testid="spnSRPProdPrice">Rp 18.999.000</div></body></html>'
        ),
        "shopee.co.id": (
            '<html><body><div class="shopee-search-item-result__item-name">Samsung Galaxy S24 Ultra</div>'
            '<div class="shopee-price">Rp 18.850.000</div></body></html>'
        ),
        "lazada.co.id": (
            '<html><body><div class="title--wFj93">Samsung Galaxy S24 Ultra Resmi</div>'
            '<div class="price--NVB62">Rp 19.150.000</div></body></html>'
        ),
    }
    calls = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        host = req.url.host or ""
        for dom, body in pages.items():
            if host.endswith(dom):
                return httpx.Response(200, text=body)
        return httpx.Response(404, text="missing")

    offers = scrape_marketplaces_worker(
        product_id,
        product_name,
        transport_factory=lambda: httpx.MockTransport(handler),
    )
    if calls != 3 or len(offers) != 3:
        raise RuntimeError(f"Expected 3 deterministic marketplace requests/offers, got calls={calls}, offers={len(offers)}")
    return offers


def raw_entry_rc03_inspect_initial_spawn_env(
    send_conn, worker_fn, product_id: str, product_name: str
) -> None:
    """Raw child entry (skips _scrub_worker_environ) to verify OS spawn allowlist before any module import."""
    try:
        spawn_env = getattr(sys, "_cb_initial_spawn_env", dict(os.environ))
        forbidden_env = (
            "DATABASE_URL",
            "TEST_DATABASE_URL",
            "JWT_SECRET_KEY",
            "OPENAI_API_KEY",
            "UNLISTED_CUSTOM_CONFIG",
        )
        inherited = [k for k in forbidden_env if k in spawn_env]
        # Note: importing `tests.*` in test harness triggers `tests._db_guard` (which uses dotenv_values),
        # whereas SQLAlchemy/psycopg2/app.db must NEVER be imported even in test harness, and production
        # `app.scrape_worker` imports neither `tests` nor `dotenv` (verified in test_f05 & subprocess check).
        forbidden_db_mods = {"app.db", "app.entities", "app.repositories", "sqlalchemy", "psycopg2"}
        imported_db = sorted(
            m for m in sys.modules if m in forbidden_db_mods or m.startswith(("sqlalchemy.", "psycopg2."))
        )
        cwd_path = Path(os.getcwd()).resolve()
        dotenv_target = Path(product_name).resolve()
        cwd_is_backend = cwd_path == dotenv_target.parent
        cwd_has_dotenv = (cwd_path / ".env").exists()
        # Honest OS-UID check: under same OS user, explicit path to backend/.env remains readable if present
        same_uid_explicit_readable = False
        if dotenv_target.is_file():
            with open(dotenv_target, "rb") as fh:
                same_uid_explicit_readable = len(fh.read(4)) >= 0

        if inherited or imported_db or cwd_is_backend or cwd_has_dotenv:
            err = {
                "status": "error",
                "error_type": "SpawnEnvLeakError",
                "message": (
                    f"inherited={inherited} imported_db={imported_db} "
                    f"cwd_is_backend={cwd_is_backend} cwd_has_dotenv={cwd_has_dotenv}"
                ),
            }
            send_conn.send_bytes(json.dumps(err).encode("utf-8"))
            sys.exit(1)

        envelope = {
            "status": "ok",
            "offers": [
                {
                    "marketplace": "Tokopedia",
                    "price": 19_000_001 if same_uid_explicit_readable else 19_000_000,
                    "url": "https://www.tokopedia.com/search?q=rc03",
                    "seller": f"env_count={len(spawn_env)}",
                    "available": True,
                    "captured_at": "2026-11-07T00:00:00+00:00",
                }
            ],
        }
        send_conn.send_bytes(json.dumps(envelope).encode("utf-8"))
    finally:
        send_conn.close()


class TestScrapeWorkerHardening(unittest.IsolatedAsyncioTestCase):
    """SEC-008 Pre-Production Hardening tests for F-01, F-03, and F-05 with real `spawn` processes."""

    async def asyncSetUp(self) -> None:
        self.sw = importlib.import_module("app.scrape_worker")
        self.ps = importlib.import_module("app.price_service")
        self.scraper = importlib.import_module("app.scraper")

    def tearDown(self) -> None:
        if hasattr(self.sw, "shutdown_default_supervisor_executor"):
            self.sw.shutdown_default_supervisor_executor()
        if hasattr(self.sw, "active_worker_pids"):
            self.assertEqual(
                self.sw.active_worker_pids(),
                [],
                "No residual subprocess worker PIDs may remain after hardening test",
            )
        self.assertEqual(
            multiprocessing.active_children(),
            [],
            "No residual worker child processes may remain after hardening test",
        )

    def test_f01_max_concurrent_env_validation(self) -> None:
        """F-01: PRICE_SCRAPE_MAX_CONCURRENT validates positive ints and rejects invalid configs."""
        self.assertTrue(hasattr(self.sw, "parse_max_concurrent_scrapes"))
        self.assertEqual(self.sw.parse_max_concurrent_scrapes(None), self.sw.DEFAULT_MAX_CONCURRENT_SCRAPES)
        self.assertGreaterEqual(self.sw.DEFAULT_MAX_CONCURRENT_SCRAPES, 1)
        self.assertEqual(self.sw.parse_max_concurrent_scrapes(""), self.sw.DEFAULT_MAX_CONCURRENT_SCRAPES)
        self.assertEqual(self.sw.parse_max_concurrent_scrapes("1"), 1)
        self.assertEqual(self.sw.parse_max_concurrent_scrapes(" 6 "), 6)
        for bad in ("0", "-1", "-99", "abc", "2.5", "true"):
            with self.assertRaises(ValueError, msg=f"Expected ValueError for {bad!r}"):
                self.sw.parse_max_concurrent_scrapes(bad)
        for bad_ctor in (0, -2, True, "4"):
            with self.assertRaises((ValueError, TypeError)):
                self.ps.PriceCache(max_concurrent=bad_ctor)  # type: ignore[arg-type]

    async def test_f01_supervisor_uses_dedicated_executor_not_default(self) -> None:
        """F01-01: Both direct flight and PriceCache run _supervise_worker_sync on dedicated thread pool."""
        loop_ident = threading.get_ident()
        observed_names: list[str] = []
        observed_idents: list[int] = []

        def record_thread() -> None:
            observed_names.append(threading.current_thread().name)
            observed_idents.append(threading.get_ident())

        await self.sw.run_isolated_scrape_flight(
            "sm-001",
            "Samsung Galaxy S24 Ultra",
            budget_seconds=5.0,
            worker_fn=worker_fast_or_hold_by_id,
            pre_spawn_hook=record_thread,
        )

        default_thread_name_holder: list[str] = []
        await asyncio.to_thread(lambda: default_thread_name_holder.append(threading.current_thread().name))

        self.assertEqual(len(observed_names), 1)
        self.assertTrue(
            observed_names[0].startswith("scrape-supervisor"),
            f"Expected dedicated scrape-supervisor thread, got {observed_names[0]!r}",
        )
        self.assertNotEqual(observed_names[0], default_thread_name_holder[0])
        self.assertNotIn(loop_ident, observed_idents)

        # Also verify PriceCache uses its own dedicated executor lifecycle
        cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=2)
        try:
            with patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
                res = await cache.get("sm-001", "Samsung Galaxy S24 Ultra")
                self.assertEqual(res.prices[0].price, 19_250_000)
                self.assertIsNotNone(cache._executor)
        finally:
            if hasattr(cache, "aclose"):
                await cache.aclose(timeout=2.0)
            elif cache._executor is not None:
                cache._executor.shutdown(wait=True, cancel_futures=True)

    async def test_f01_persistence_not_blocked_by_saturated_supervisor_executor(self) -> None:
        """F01-03: Saturated dedicated supervisor threads do not delay default-executor DB persistence."""
        with tempfile.TemporaryDirectory() as pid_dir:
            cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=2)
            f1 = None
            f2 = None
            try:
                f1 = asyncio.create_task(cache.get("slow-1", pid_dir))
                f2 = asyncio.create_task(cache.get("slow-2", pid_dir))

                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    if (Path(pid_dir) / "slow-1.pid").is_file() and (Path(pid_dir) / "slow-2.pid").is_file():
                        break
                    await asyncio.sleep(0.02)
                self.assertTrue((Path(pid_dir) / "slow-1.pid").is_file())
                self.assertTrue((Path(pid_dir) / "slow-2.pid").is_file())

                # Both supervisor threads in `cache` are now 100% occupied waiting on slow-1 & slow-2.
                # Parent persistence on default executor must still run immediately without queuing behind them!
                save_threads: list[str] = []

                def record_save(**kwargs) -> bool:
                    save_threads.append(threading.current_thread().name)
                    return True

                sample_resp = self.scraper.build_price_response("sm-001", "Phone", [])
                t0 = time.monotonic()
                with patch("app.repositories.price_repo.save_price_snapshot", side_effect=record_save):
                    await self.scraper._run_blocking(
                        self.scraper._save_snapshots,
                        "sm-001",
                        sample_resp.prices,
                        "2026-11-07T00:00:00+00:00",
                    )
                save_elapsed = time.monotonic() - t0
                self.assertLess(save_elapsed, 0.3)
                self.assertEqual(len(save_threads), 3)
                self.assertTrue(all(not name.startswith("scrape-supervisor") for name in save_threads))
            finally:
                for task in (f1, f2):
                    if task is not None and not task.done():
                        task.cancel()
                if f1 is not None and f2 is not None:
                    await asyncio.gather(f1, f2, return_exceptions=True)
                if hasattr(cache, "aclose"):
                    await cache.aclose(timeout=3.0)
                elif cache._executor is not None:
                    cache._executor.shutdown(wait=True, cancel_futures=True)

    async def test_f01_overload_rejects_without_spawning_extra_worker_process(self) -> None:
        """F01-02 & F01-04: Capacity full -> immediate ScrapeOverloadError, 0 extra workers, coalescing intact."""
        self.assertTrue(hasattr(self.sw, "ScrapeOverloadError"))
        with tempfile.TemporaryDirectory() as pid_dir:
            cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=2)
            try:
                t1 = asyncio.create_task(cache.get("slow-1", pid_dir))
                t2 = asyncio.create_task(cache.get("slow-2", pid_dir))

                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    if (Path(pid_dir) / "slow-1.pid").is_file() and (Path(pid_dir) / "slow-2.pid").is_file():
                        break
                    await asyncio.sleep(0.02)
                pid1 = int((Path(pid_dir) / "slow-1.pid").read_text(encoding="utf-8").strip())
                pid2 = int((Path(pid_dir) / "slow-2.pid").read_text(encoding="utf-8").strip())
                self.assertEqual(len(self.sw.active_worker_pids()), 2)
                self.assertEqual(multiprocessing.active_children(), [])

                # Coalesced waiter on existing slow-1 flight MUST join without consuming a 3rd slot
                t1_joined = asyncio.create_task(cache.get("slow-1", pid_dir))
                await asyncio.sleep(0.02)
                self.assertFalse(t1_joined.done())

                # Distinct 3rd key MUST fail immediately without queueing or spawning a 3rd worker
                t0 = time.monotonic()
                with self.assertRaises(self.sw.ScrapeOverloadError):
                    await cache.get("slow-3", pid_dir)
                self.assertLess(time.monotonic() - t0, 0.1)
                self.assertFalse((Path(pid_dir) / "slow-3.pid").exists())
                self.assertEqual(len(self.sw.active_worker_pids()), 2)
                self.assertEqual(multiprocessing.active_children(), [])

                # Cancel slow-1 waiters -> slot freed once pid1 stops -> sm-001 succeeds!
                t1.cancel()
                t1_joined.cancel()
                await asyncio.gather(t1, t1_joined, return_exceptions=True)
                self.assertFalse(is_os_pid_running(pid1))

                with patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
                    ok = await cache.get("sm-001", "Phone")
                    self.assertEqual(ok.prices[0].price, 19_250_000)

                t2.cancel()
                await asyncio.gather(t2, return_exceptions=True)
                self.assertFalse(is_os_pid_running(pid2))
            finally:
                if hasattr(cache, "aclose"):
                    await cache.aclose(timeout=3.0)
                elif cache._executor is not None:
                    cache._executor.shutdown(wait=True, cancel_futures=True)

    async def test_f03_01_shutdown_without_active_flights_rejects_new_and_cached_requests(self) -> None:
        """F03-01 & F03-02: Shutdown with 0 active flights closes cleanly and blocks new requests."""
        cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=2)
        with patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
            await cache.get("sm-001", "Phone")
        drain = await cache.aclose(timeout=1.0)
        self.assertTrue(drain.clean)
        self.assertEqual(drain.quarantined_keys, ())
        with self.assertRaises(self.sw.ScrapeOverloadError):
            await cache.get("sm-001", "Phone")
        with self.assertRaises(self.sw.ScrapeOverloadError):
            await cache.get("sm-002", "Other")

    async def test_f03_02_shutdown_with_one_normal_running_worker_stops_immediately(self) -> None:
        """F03-01 & F03-04: Shutdown interrupts normal 35s worker immediately without waiting 35s."""
        with tempfile.TemporaryDirectory() as pid_dir:
            cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=2)
            req = asyncio.create_task(cache.get("slow-1", pid_dir))
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline and not (Path(pid_dir) / "slow-1.pid").is_file():
                await asyncio.sleep(0.02)
            pid = int((Path(pid_dir) / "slow-1.pid").read_text(encoding="utf-8").strip())
            self.assertTrue(is_os_pid_running(pid))

            t0 = time.monotonic()
            drain = await cache.aclose(timeout=3.0)
            elapsed = time.monotonic() - t0

            self.assertLess(elapsed, 2.5, "Shutdown must terminate active worker promptly, not wait 35s")
            self.assertTrue(drain.clean)
            self.assertFalse(is_os_pid_running(pid))
            self.assertEqual(multiprocessing.active_children(), [])
            await asyncio.gather(req, return_exceptions=True)

    async def test_f03_03_shutdown_with_multiple_workers_cpu_spin_and_timeout_worker(self) -> None:
        """F03-03 & F03-04: Shutdown cleans up multiple active workers including SIGTERM-ignoring and timing-out ones."""
        with tempfile.NamedTemporaryFile("w+", delete=False) as spin_tf:
            spin_pid_file = spin_tf.name
        try:
            with tempfile.TemporaryDirectory() as pid_dir:
                cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=4)
                cache_spin = self.ps.PriceCache(worker_fn=worker_t06_cpu_hang_ignore_sigterm, max_concurrent=2)
                # Start 2 normal 35s workers + 1 SIGTERM-ignoring CPU-spinning 35s worker deterministically
                r1 = asyncio.create_task(cache.get("slow-1", pid_dir))
                r2 = asyncio.create_task(cache.get("slow-2", pid_dir))
                r_spin = asyncio.create_task(cache_spin.get("sm-001", spin_pid_file))

                deadline = time.monotonic() + 8.0
                while time.monotonic() < deadline:
                    if (
                        (Path(pid_dir) / "slow-1.pid").is_file()
                        and (Path(pid_dir) / "slow-2.pid").is_file()
                        and Path(spin_pid_file).read_text(encoding="utf-8").strip()
                    ):
                        break
                    await asyncio.sleep(0.02)

                self.assertTrue((Path(pid_dir) / "slow-1.pid").is_file())
                self.assertTrue((Path(pid_dir) / "slow-2.pid").is_file())
                self.assertTrue(bool(Path(spin_pid_file).read_text(encoding="utf-8").strip()))
                pid1 = int((Path(pid_dir) / "slow-1.pid").read_text(encoding="utf-8").strip())
                pid2 = int((Path(pid_dir) / "slow-2.pid").read_text(encoding="utf-8").strip())
                pid_spin = int(Path(spin_pid_file).read_text(encoding="utf-8").strip())
                self.assertTrue(is_os_pid_running(pid1))
                self.assertTrue(is_os_pid_running(pid2))
                self.assertTrue(is_os_pid_running(pid_spin))

                # Also start a short-budget timing-out worker only AFTER 35s workers are confirmed active
                with patch.object(self.scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", 1.8):
                    r_short = asyncio.create_task(cache.get("slow-3", pid_dir))
                    short_deadline = time.monotonic() + 5.0
                    while time.monotonic() < short_deadline and not (Path(pid_dir) / "slow-3.pid").is_file():
                        await asyncio.sleep(0.02)
                    self.assertTrue((Path(pid_dir) / "slow-3.pid").is_file())
                    pid3 = int((Path(pid_dir) / "slow-3.pid").read_text(encoding="utf-8").strip())

                    # Measure ONLY shutdown elapsed time (isolated from setup spawn latency)
                    t_close = time.monotonic()
                    close_both = asyncio.gather(cache.aclose(timeout=3.0), cache_spin.aclose(timeout=3.0))
                    close_task = asyncio.ensure_future(close_both)
                    await asyncio.sleep(0)
                    with self.assertRaises(self.sw.ScrapeOverloadError):
                        await cache.get("sm-002", "RejectedDuringClosing")
                    d1, d2 = await close_task
                    shutdown_elapsed = time.monotonic() - t_close

                    self.assertLess(
                        shutdown_elapsed,
                        2.5,
                        "Multi-worker shutdown including 35s CPU-spinning worker must obey bounded escalation",
                    )
                    self.assertTrue(d1.clean)
                    self.assertTrue(d2.clean)
                    self.assertEqual(d1.quarantined_keys, ())
                    self.assertEqual(d2.quarantined_keys, ())
                    self.assertFalse(is_os_pid_running(pid1))
                    self.assertFalse(is_os_pid_running(pid2))
                    self.assertFalse(is_os_pid_running(pid3))
                    self.assertFalse(is_os_pid_running(pid_spin))
                    self.assertEqual(multiprocessing.active_children(), [])
                    self.assertEqual(self.sw.active_worker_pids(), [])
                    self.assertEqual(cache._active_permits, 0)
                    self.assertEqual(cache_spin._active_permits, 0)
                    self.assertIsNone(cache._executor)
                    self.assertIsNone(cache_spin._executor)
                    with self.assertRaises(self.sw.ScrapeOverloadError):
                        await cache_spin.get("sm-002", "PostClose")
                    await asyncio.gather(r1, r2, r_short, r_spin, return_exceptions=True)
        finally:
            Path(spin_pid_file).unlink(missing_ok=True)

    async def test_f03_04_shutdown_during_stopping_and_after_cleanup_error(self) -> None:
        """F03-03: Shutdown handles flights already in STOPPING and reports/reaps QUARANTINED flights."""
        # 1) Shutdown while flight is in STOPPING
        teardown_entered = asyncio.Event()
        release_teardown = asyncio.Event()

        async def stopping_flight(product_id, name, *, cancel_event=None, on_stopping=None, **kwargs):
            try:
                await asyncio.Event().wait()
            finally:
                if on_stopping is not None:
                    on_stopping()
                teardown_entered.set()
                await release_teardown.wait()

        cache_stopping = self.ps.PriceCache(max_concurrent=2)
        with patch.object(self.sw, "run_isolated_scrape_flight", side_effect=stopping_flight):
            w = asyncio.create_task(cache_stopping.get("sm-001", "Phone"))
            await asyncio.sleep(0.01)
            w.cancel()
            await teardown_entered.wait()
            self.assertEqual(cache_stopping._inflight[("sm-001", "Phone")].state, "STOPPING")
            close_task = asyncio.create_task(cache_stopping.aclose(timeout=2.0))
            await asyncio.sleep(0.02)
            # New flight while CLOSING must be rejected immediately
            with self.assertRaises(self.sw.ScrapeOverloadError):
                await cache_stopping.get("sm-002", "Other")
            release_teardown.set()
            drain_res = await close_task
            self.assertTrue(drain_res.clean)
            await asyncio.gather(w, return_exceptions=True)

        # 2) Shutdown after cleanup error (QUARANTINED flight still unkillable vs exiting during shutdown)
        class StubUnkillableProc:
            pid = 77777
            exitcode = None
            closed = False

            def is_alive(self) -> bool:
                return self.exitcode is None

            def terminate(self) -> None:
                pass

            def kill(self) -> None:
                pass

            def join(self, timeout: float | None = None) -> None:
                pass

            def close(self) -> None:
                self.closed = True

        stub_proc = StubUnkillableProc()

        async def fail_cleanup(*args, **kwargs):
            raise self.sw.ScrapeWorkerCleanupError(
                "simulated unkillable OS process",
                worker_pid=stub_proc.pid,
                unreaped_proc=stub_proc,
            )

        cache_q = self.ps.PriceCache(max_concurrent=2)
        with patch.object(self.sw, "run_isolated_scrape_flight", side_effect=fail_cleanup):
            with self.assertRaises(self.sw.ScrapeWorkerCleanupError):
                await cache_q.get("sm-001", "Phone")
        self.assertEqual(cache_q._inflight[("sm-001", "Phone")].state, "QUARANTINED")

        t0 = time.monotonic()
        drain_unclean = await cache_q.aclose(timeout=0.1)
        self.assertLess(time.monotonic() - t0, 0.8)
        self.assertFalse(drain_unclean.clean)
        self.assertEqual(drain_unclean.quarantined_keys, (("sm-001", "Phone"),))

        # Once OS process finally exits, reopening and closing reaps it cleanly
        stub_proc.exitcode = -9
        cache_q.open()
        drain_clean = await cache_q.aclose(timeout=0.5)
        self.assertTrue(drain_clean.clean)
        self.assertTrue(stub_proc.closed)
        self.assertEqual(drain_clean.quarantined_keys, ())

    def test_f03_05_fastapi_lifespan_drains_active_worker_and_reopens_cleanly(self) -> None:
        """F03-01: FastAPI lifespan exit triggers price_cache.aclose() and next lifespan re-opens cleanly."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.routers import prices

        test_cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=2)
        with patch.object(prices, "price_cache", test_cache), patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=False
        ):
            with TestClient(app) as client:
                resp = client.get("/api/prices/sm-001")
                self.assertEqual(resp.status_code, 200)

            # Exiting TestClient ran lifespan shutdown -> cache is CLOSED
            with self.assertRaises(self.sw.ScrapeOverloadError):
                asyncio.run(test_cache.get("sm-001", "Samsung Galaxy S24 Ultra"))

            # Entering a new lifespan cycle re-opens cache cleanly
            with TestClient(app) as client2:
                resp2 = client2.get("/api/prices/sm-001")
                self.assertEqual(resp2.status_code, 200)

    async def test_f05_worker_import_chain_and_parent_environ_safety(self) -> None:
        """F05-01..03: Worker never imports DB/dotenv or reads .env; parent os.environ never mutated."""
        import subprocess

        backend_dir = Path(__file__).resolve().parent.parent
        probe_code = (
            "import builtins, os, sys, httpx\n"
            "opened = []\n"
            "orig_open = builtins.open\n"
            "def spy_open(file, *a, **kw):\n"
            "    opened.append(str(file))\n"
            "    return orig_open(file, *a, **kw)\n"
            "builtins.open = spy_open\n"
            "import app.scrape_worker as sw\n"
            "tx = lambda: httpx.MockTransport(lambda req: httpx.Response(200, text='<html></html>'))\n"
            "sw.scrape_marketplaces_worker('sm-001', 'Samsung Galaxy S24 Ultra', transport_factory=tx)\n"
            "forbidden_mods = {'app.db', 'app.entities', 'app.repositories', 'sqlalchemy', 'psycopg2', 'dotenv'}\n"
            "leaked = sorted(m for m in sys.modules if m in forbidden_mods or m.startswith(('sqlalchemy.', 'psycopg2.', 'dotenv.')))\n"
            "dotenv_reads = [p for p in opened if p.replace('\\\\', '/').endswith('/.env') or p == '.env']\n"
            "assert not leaked, f'Forbidden modules imported: {leaked}'\n"
            "assert not dotenv_reads, f'.env read in worker: {dotenv_reads}'\n"
            "print('F05_IMPORT_CHAIN_CLEAN')\n"
        )
        env = os.environ.copy()
        env["DATABASE_URL"] = ""
        proc = subprocess.run(
            [sys.executable, "-c", probe_code],
            cwd=str(backend_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("F05_IMPORT_CHAIN_CLEAN", proc.stdout)

        # Verify parent os.environ is never mutated during child spawn while child scrubs secrets
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://u:secret@localhost:5432/comparebuy_test",
                "TEST_DATABASE_URL": "postgresql://u:secret@localhost:5432/comparebuy_test",
                "JWT_SECRET_KEY": "dummy-secret",
                "DB_PASSWORD": "dummy-password",
            },
        ):
            before_db = os.environ["DATABASE_URL"]
            before_secret = os.environ["JWT_SECRET_KEY"]
            outcome = await self.sw.run_isolated_scrape_flight(
                "sm-001",
                "Samsung Galaxy S24 Ultra",
                budget_seconds=5.0,
                worker_fn=worker_f05_audit_child_env,
            )
            self.assertEqual(len(outcome.offers), 1)
            self.assertEqual(os.environ["DATABASE_URL"], before_db)
            self.assertEqual(os.environ["JWT_SECRET_KEY"], before_secret)

    async def test_rc01_deterministic_worker_resource_and_admission_invariants(self) -> None:
        """RC-01: Deterministic 3-marketplace worker profile, fast overload reject, and slot hold until stop."""
        outcome = await self.sw.run_isolated_scrape_flight(
            "sm-001",
            "Samsung Galaxy S24 Ultra",
            budget_seconds=10.0,
            worker_fn=worker_rc01_three_marketplaces_profiled,
        )
        self.assertEqual(len(outcome.offers), 3)
        self.assertTrue(outcome.reaped)
        self.assertEqual(outcome.exitcode, 0)
        self.assertLess(outcome.finished_at - outcome.started_at, 8.0)

        with tempfile.TemporaryDirectory() as pid_dir:
            cache = self.ps.PriceCache(worker_fn=worker_fast_or_hold_by_id, max_concurrent=2)
            try:
                with patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
                    cached = await cache.get("sm-001", "CachedProduct")
                    self.assertEqual(cached.prices[0].price, 19_250_000)

                t1 = asyncio.create_task(cache.get("slow-1", pid_dir))
                t2 = asyncio.create_task(cache.get("slow-2", pid_dir))
                deadline = time.monotonic() + 6.0
                while time.monotonic() < deadline:
                    if (Path(pid_dir) / "slow-1.pid").is_file() and (Path(pid_dir) / "slow-2.pid").is_file():
                        break
                    await asyncio.sleep(0.02)
                self.assertEqual(cache._active_permits, 2)

                # Cache hit at full capacity uses 0 permits; 3rd miss rejects immediately (no queue!)
                hit = await cache.get("sm-001", "CachedProduct")
                self.assertEqual(hit.prices[0].price, 19_250_000)
                t_rej = time.monotonic()
                with self.assertRaises(self.sw.ScrapeOverloadError):
                    await cache.get("slow-3", pid_dir)
                self.assertLess(time.monotonic() - t_rej, 0.25)
                self.assertFalse((Path(pid_dir) / "slow-3.pid").exists())
            finally:
                drain = await cache.aclose(timeout=3.0)
                self.assertTrue(drain.clean)
                self.assertEqual(cache._active_permits, 0)
                await asyncio.gather(t1, t2, return_exceptions=True)

    async def test_rc03_child_spawn_allowlist_blocks_secret_inheritance_before_entry(self) -> None:
        """RC-03: Child receives allowlisted env at OS spawn (before _worker_entry) without mutating parent."""
        backend_dir = Path(__file__).resolve().parent.parent
        dotenv_file = backend_dir / ".env"
        injected = {
            "DATABASE_URL": "postgresql://dev_user:dev_secret@localhost:5432/comparebuy",
            "TEST_DATABASE_URL": "postgresql://test_user:test_secret@localhost:5432/comparebuy_test",
            "JWT_SECRET_KEY": "jwt-super-secret",
            "OPENAI_API_KEY": "sk-live-secret",
            "UNLISTED_CUSTOM_CONFIG": "parent-only-config",
        }
        with patch.dict(os.environ, injected):
            env_snapshot = {k: os.environ[k] for k in injected}
            outcome = await self.sw.run_isolated_scrape_flight(
                "sm-001",
                str(dotenv_file),
                budget_seconds=8.0,
                worker_fn=worker_f05_audit_child_env,
                _entry_override=raw_entry_rc03_inspect_initial_spawn_env,
            )
            built = self.sw.build_worker_env()
            for k in injected:
                self.assertNotIn(k, built)
            self.assertTrue(set(built.keys()).issubset(self.sw.WORKER_ENV_ALLOWLIST | set(self.sw.WORKER_FIXED_ENV)))
            self.assertEqual(len(outcome.offers), 1)
            # Document verified OS-UID boundary: if backend/.env exists on host, same OS user can read explicit path
            expected_price = 19_000_001 if dotenv_file.is_file() else 19_000_000
            self.assertEqual(outcome.offers[0].price, expected_price)
            # Parent os.environ must remain 100% unmutated
            for k, v in env_snapshot.items():
                self.assertEqual(os.environ[k], v)


if __name__ == "__main__":
    unittest.main()
