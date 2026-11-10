"""SEC-008: deterministic cache, process-isolation orchestration, cancellation, session, DB guard, and API regressions."""
import asyncio
import importlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from tests._db_guard import enforce_safe_test_db_env

enforce_safe_test_db_env()

from app import scraper
from app.db import get_db
from app.main import app
from app.models import MarketplacePrice, PriceResponse
from app.routers import prices
from app.security import check_price_rate_limit
from app.security.rate_limiter import price_rate_limiter


def load_scrape_worker(testcase: unittest.TestCase):
    spec = importlib.util.find_spec("app.scrape_worker")
    testcase.assertIsNotNone(spec, "SEC-008 AC-08 worker module app.scrape_worker is missing")
    return importlib.import_module("app.scrape_worker")


def scraped_offer(marketplace="Tokopedia", price=19_499_000, url="https://www.tokopedia.com/search?q=sm-001"):
    return MarketplacePrice(
        marketplace=marketplace,
        price=price,
        url=url,
        seller=f"{marketplace} Seller",
        available=True,
        source="scraped",
        captured_at="2026-11-07T00:00:00+00:00",
    )


def worker_outcome(sw, offers=None, pid=42424, started_at=100.0, finished_at=100.2, budget=35.0):
    return sw.WorkerFlightOutcome(
        offers=list(offers) if offers is not None else [scraped_offer()],
        worker_pid=pid,
        exitcode=0,
        started_at=started_at,
        finished_at=finished_at,
        deadline=started_at + budget,
        cleanup_reserve=min(2.0, max(0.05, budget * 0.25)),
        reaped=True,
    )


def mock_marketplaces(stack, value=None):
    return [
        stack.enter_context(patch.object(scraper, name, AsyncMock(return_value=value)))
        for name in ("_scrape_tokopedia", "_scrape_shopee", "_scrape_lazada")
    ]


class TestPriceCache(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("app.price_service"),
            "SEC-008 cache orchestration wrapper is missing",
        )
        self.service = importlib.import_module("app.price_service")
        self.sw = load_scrape_worker(self)
        self.cache = self.service.PriceCache()
        price_rate_limiter.reset()

    async def asyncTearDown(self):
        price_rate_limiter.reset()
        await self.cache.aclose(timeout=1.0)

    async def test_cache_miss_hit_ttl_and_deep_copy(self):
        with patch.object(self.service, "monotonic", return_value=100) as clock, patch.object(
            self.sw,
            "run_isolated_scrape_flight",
            AsyncMock(return_value=worker_outcome(self.sw)),
        ) as fetch, patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
            first = await self.cache.get("sm-001", "Phone")
            first.prices[0].price = 1
            first.prices.clear()
            clock.return_value = 399.999
            hit = await self.cache.get("sm-001", "Phone")
            self.assertEqual(len(hit.prices), 3)
            self.assertGreater(hit.prices[0].price, 1)
            fetch.assert_awaited_once()
            clock.return_value = 400
            await self.cache.get("sm-001", "Phone")
            self.assertEqual(fetch.await_count, 2)
        self.assertEqual(self.service.PRICE_CACHE_TTL_SECONDS, 300)
        self.assertFalse(self.cache._inflight)

    async def test_single_flight_and_product_parameter_isolation(self):
        started = asyncio.Event()
        release = asyncio.Event()

        async def fetch(product_id, name, **kwargs):
            started.set()
            await release.wait()
            return worker_outcome(self.sw, offers=[scraped_offer(url=f"https://www.tokopedia.com/search?q={product_id}")])

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=fetch)) as fetch_mock, patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=False
        ):
            tasks = [asyncio.create_task(self.cache.get("sm-001", "Phone")) for _ in range(10)]
            await started.wait()
            tasks += [
                asyncio.create_task(self.cache.get("sm-002", "Other")),
                asyncio.create_task(self.cache.get("sm-001", "Renamed")),
            ]
            await asyncio.sleep(0)
            release.set()
            results = await asyncio.gather(*tasks)
            self.assertEqual(fetch_mock.await_count, 3)
            self.assertEqual(results[-2].product_id, "sm-002")
            self.assertEqual(results[-1].product_name, "Renamed")
            results[0].prices.clear()
            self.assertGreaterEqual(len(results[1].prices), 1)
        self.assertFalse(self.cache._inflight)

    async def test_expired_concurrent_requests_refresh_once(self):
        with patch.object(self.service, "monotonic", return_value=0) as clock, patch.object(
            self.sw,
            "run_isolated_scrape_flight",
            AsyncMock(return_value=worker_outcome(self.sw)),
        ) as fetch, patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
            await self.cache.get("sm-001", "Phone")
            clock.return_value = 300
            await asyncio.gather(*(self.cache.get("sm-001", "Phone") for _ in range(20)))
            self.assertEqual(fetch.await_count, 2)

    async def test_exception_propagates_to_waiters_and_retry_is_not_cached(self):
        async def fail(*args, **kwargs):
            await asyncio.sleep(0)
            raise self.sw.ScrapeWorkerError("worker crashed")

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=fail)) as fetch, patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=False
        ) as save:
            results = await asyncio.gather(
                *(self.cache.get("sm-001", "Phone") for _ in range(5)),
                return_exceptions=True,
            )
            self.assertTrue(all(isinstance(result, RuntimeError) for result in results))
            fetch.assert_awaited_once()
            self.assertFalse(self.cache._cache)
            self.assertFalse(self.cache._inflight)
            save.assert_not_called()
            fetch.side_effect = None
            fetch.return_value = worker_outcome(self.sw)
            await self.cache.get("sm-001", "Phone")
            self.assertEqual(fetch.await_count, 2)

    async def test_cancelled_leader_does_not_cancel_another_waiter(self):
        started, release = asyncio.Event(), asyncio.Event()

        async def fetch(*args, **kwargs):
            started.set()
            await release.wait()
            return worker_outcome(self.sw)

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=fetch)) as fetch_mock, patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=False
        ):
            leader = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await started.wait()
            waiter = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await asyncio.sleep(0)
            leader.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await leader
            release.set()
            self.assertEqual((await waiter).product_id, "sm-001")
            fetch_mock.assert_awaited_once()
        self.assertFalse(self.cache._inflight)

    async def test_last_waiter_cancellation_drains_scrapers_without_persistence(self):
        started = asyncio.Event()
        cleaned = asyncio.Event()

        async def hang(product_id, name, *, cancel_event=None, **kwargs):
            started.set()
            try:
                while cancel_event is None or not cancel_event.is_set():
                    await asyncio.sleep(0.005)
                raise asyncio.CancelledError
            finally:
                cleaned.set()

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=hang)), patch(
            "app.repositories.price_repo.save_price_snapshot"
        ) as save:
            request = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await started.wait()
            request.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await request
            self.assertTrue(cleaned.is_set())
            self.assertFalse(self.cache._inflight)
            self.assertFalse(self.cache._cache)
            save.assert_not_called()

    async def test_fallback_persistence_only_on_miss_and_after_expiry(self):
        with patch.object(
            self.sw,
            "run_isolated_scrape_flight",
            AsyncMock(return_value=worker_outcome(self.sw, offers=[])),
        ) as fetch, patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=True
        ) as save, patch.object(self.service, "monotonic", return_value=0) as clock:
            first = await self.cache.get("sm-001", "Phone")
            await self.cache.get("sm-001", "Phone")
            self.assertEqual(save.call_count, 3)
            for call in save.call_args_list:
                self.assertEqual(call.kwargs["source"], "fallback")
                self.assertIsNotNone(call.kwargs["captured_at"])
            self.assertTrue(all(p.source == "fallback" and p.captured_at is None for p in first.prices))
            clock.return_value = 300
            await self.cache.get("sm-001", "Phone")
            self.assertEqual(save.call_count, 6)
            self.assertEqual(fetch.await_count, 2)

    async def test_total_timeout_raises_error_without_caching_or_persistence(self):
        """Updated for approved D7: total flight timeout aborts worker, rejects partial/fallback, 0 cache, 0 DB write."""
        async def timed_out_flight(*args, **kwargs):
            raise self.sw.ScrapeTimeoutError(
                "Scrape worker exceeded 35.0s budget",
                budget=35.0,
                elapsed=33.01,
                worker_pid=99999,
                exitcode=1,
                worker_stopped=True,
                reaped=True,
                within_budget=True,
            )

        with patch.object(
            self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=timed_out_flight)
        ) as fetch, patch("app.repositories.price_repo.save_price_snapshot", return_value=True) as save:
            with self.assertRaises(self.sw.ScrapeTimeoutError):
                await self.cache.get("sm-001", "Phone")
            self.assertFalse(self.cache._inflight)
            self.assertFalse(self.cache._cache)
            save.assert_not_called()
            self.assertEqual(fetch.await_count, 1)

    async def test_uncaught_timeout_does_not_poison_cache(self):
        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=TimeoutError)):
            with self.assertRaises(TimeoutError):
                await self.cache.get("sm-001", "Phone")
        self.assertFalse(self.cache._cache)
        self.assertFalse(self.cache._inflight)

    async def test_simultaneous_api_requests_share_scraping(self):
        async def fetch(product_id, name, **kwargs):
            await asyncio.sleep(0.01)
            return worker_outcome(self.sw)

        def no_db():
            yield None

        app.dependency_overrides[get_db] = no_db
        app.dependency_overrides[check_price_rate_limit] = lambda: "testclient"
        try:
            with patch.object(prices, "price_cache", self.cache), patch.object(
                self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=fetch)
            ) as fetch_mock, patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    results = await asyncio.gather(
                        *(client.get("/api/prices/sm-001") for _ in range(10)),
                        client.get("/api/prices/sm-002"),
                    )
            self.assertTrue(all(result.status_code == 200 for result in results))
            self.assertEqual(fetch_mock.await_count, 2)
            self.assertEqual(results[-1].json()["product_id"], "sm-002")
            self.assertFalse(self.cache._inflight)
        finally:
            app.dependency_overrides.pop(check_price_rate_limit, None)
            app.dependency_overrides.pop(get_db, None)

    # ── Additional AC-08 Single-Flight / Generation / Race Matrix Tests ──

    async def test_t08_repeated_cancel_on_last_waiter_keeps_state_consistent(self):
        """T-08: Repeated cancellation during last-waiter teardown still drains worker before releasing flight."""
        in_teardown = asyncio.Event()
        allow_exit = asyncio.Event()

        async def cancel_aware_worker(product_id, name, *, cancel_event=None, **kwargs):
            try:
                await asyncio.Event().wait()
            finally:
                in_teardown.set()
                await allow_exit.wait()

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=cancel_aware_worker)), patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=True
        ) as save:
            w1 = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            w2 = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await asyncio.sleep(0.01)

            w1.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await w1
            self.assertFalse(in_teardown.is_set(), "Worker must keep running while w2 still waits")

            w2.cancel()
            await in_teardown.wait()
            # Flight must remain tracked as STOPPING while worker teardown is still active!
            self.assertIn(("sm-001", "Phone"), self.cache._inflight)
            self.assertEqual(self.cache._inflight[("sm-001", "Phone")].state, "STOPPING")
            w2.cancel()  # repeated cancel during drain
            await asyncio.sleep(0)
            allow_exit.set()
            with self.assertRaises(asyncio.CancelledError):
                await w2

            self.assertFalse(self.cache._inflight)
            self.assertFalse(self.cache._cache)
            save.assert_not_called()

    async def test_t09_superseded_or_aborted_generation_never_writes_cache_or_db(self):
        """T-09: If cancel_event is triggered right as worker returns, parent rejects persistence and cache publish."""
        async def late_return_after_cancel(product_id, name, *, cancel_event=None, **kwargs):
            cancel_event.set()
            return worker_outcome(self.sw, offers=[scraped_offer(price=18_777_000)])

        with patch.object(
            self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=late_return_after_cancel)
        ), patch("app.repositories.price_repo.save_price_snapshot", return_value=True) as save:
            with self.assertRaises(asyncio.CancelledError):
                await self.cache.get("sm-001", "Phone")
            self.assertFalse(self.cache._cache)
            self.assertFalse(self.cache._inflight)
            save.assert_not_called()

    async def test_t10_multi_waiter_timeout_transitions_and_single_worker(self):
        """T-10: 8 waiters on same key share 1 physical flight, transition RUNNING->STOPPING->STOPPED, 0 cache/DB."""
        observed_states = []
        started = asyncio.Event()
        release_timeout = asyncio.Event()

        async def slow_timeout(product_id, name, **kwargs):
            flight = self.cache._inflight[("sm-001", "Phone")]
            observed_states.append(flight.state)
            started.set()
            await release_timeout.wait()
            raise self.sw.ScrapeTimeoutError(
                "Timed out",
                budget=35.0,
                elapsed=33.1,
                worker_pid=55555,
                exitcode=1,
                worker_stopped=True,
                reaped=True,
                within_budget=True,
            )

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=slow_timeout)) as fetch, patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=True
        ) as save:
            waiters = [asyncio.create_task(self.cache.get("sm-001", "Phone")) for _ in range(8)]
            await started.wait()
            await asyncio.sleep(0)
            flight_ref = self.cache._inflight[("sm-001", "Phone")]
            self.assertEqual(flight_ref.waiters, 8)
            release_timeout.set()
            outcomes = await asyncio.gather(*waiters, return_exceptions=True)

        self.assertEqual(observed_states, ["RUNNING"])
        self.assertEqual(flight_ref.state, "STOPPED")
        self.assertEqual(fetch.await_count, 1)
        self.assertTrue(all(isinstance(o, self.sw.ScrapeTimeoutError) for o in outcomes))
        self.assertFalse(self.cache._inflight)
        self.assertFalse(self.cache._cache)
        save.assert_not_called()

    async def test_t11_request_during_stopping_waits_for_old_exit_without_duplicate_spawn(self):
        """T-11: Replacement request arriving during STOPPING waits for old stop confirmation; max active=1."""
        teardown_started = asyncio.Event()
        finish_teardown = asyncio.Event()
        active_workers = 0
        max_concurrent_workers = 0
        call_num = 0

        async def controlled_flight(product_id, name, **kwargs):
            nonlocal active_workers, max_concurrent_workers, call_num
            call_num += 1
            my_call = call_num
            active_workers += 1
            max_concurrent_workers = max(max_concurrent_workers, active_workers)
            try:
                if my_call == 1:
                    try:
                        await asyncio.Event().wait()
                    finally:
                        teardown_started.set()
                        await finish_teardown.wait()
                return worker_outcome(self.sw, offers=[scraped_offer(price=18_500_000)])
            finally:
                active_workers -= 1

        with patch.object(
            self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=controlled_flight)
        ) as fetch, patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
            first_req = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await asyncio.sleep(0.01)
            first_req.cancel()
            await teardown_started.wait()

            # Start replacement request WHILE Flight #1 is still in STOPPING
            replacement_req = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await asyncio.sleep(0.02)
            # Flight #2 MUST NOT have spawned yet because Flight #1 has not confirmed stop!
            self.assertEqual(fetch.await_count, 1)
            self.assertEqual(max_concurrent_workers, 1)

            finish_teardown.set()
            with self.assertRaises(asyncio.CancelledError):
                await first_req
            rep_res = await replacement_req

        self.assertEqual(max_concurrent_workers, 1)
        self.assertEqual(fetch.await_count, 2)
        self.assertEqual(rep_res.prices[0].price, 18_500_000)
        self.assertFalse(self.cache._inflight)

    async def test_t15_cancel_replacement_and_old_completion_race_no_stale_overwrite(self):
        """T-15: Old cancelled generation completing during teardown cannot overwrite new generation's cache."""
        gen1_in_flight = asyncio.Event()
        release_gen1 = asyncio.Event()
        calls = 0

        async def racing_worker(product_id, name, *, cancel_event=None, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                gen1_in_flight.set()
                await release_gen1.wait()
                # Simulate old worker trying to return stale Rp 19.999.000 right as cancel happened
                return worker_outcome(self.sw, offers=[scraped_offer(price=19_999_000)])
            return worker_outcome(self.sw, offers=[scraped_offer(price=18_111_000)])

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=racing_worker)), patch(
            "app.repositories.price_repo.save_price_snapshot", return_value=True
        ) as save:
            req1 = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await gen1_in_flight.wait()
            req1.cancel()
            await asyncio.sleep(0)
            req2 = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            release_gen1.set()

            with self.assertRaises(asyncio.CancelledError):
                await req1
            res2 = await req2
            cached = await self.cache.get("sm-001", "Phone")

        self.assertEqual(res2.prices[0].price, 18_111_000)
        self.assertEqual(cached.prices[0].price, 18_111_000)
        # Only Generation 2 persisted its 3 offers; Generation 1 wrote 0
        self.assertEqual(save.call_count, 3)

    async def test_t18_cancellation_during_parent_db_persistence_drains_session_cleanly(self):
        """T-18: If caller cancels after worker succeeded while parent DB persistence runs, DB worker drains safely."""
        db_started = threading.Event()
        db_release = threading.Event()
        db_closed = threading.Event()
        ready_async = asyncio.Event()
        loop = asyncio.get_running_loop()

        def blocking_save(**kwargs):
            db_started.set()
            loop.call_soon_threadsafe(ready_async.set)
            try:
                db_release.wait(2.0)
                return True
            finally:
                db_closed.set()

        with patch.object(
            self.sw,
            "run_isolated_scrape_flight",
            AsyncMock(return_value=worker_outcome(self.sw, offers=[scraped_offer(price=18_900_000)])),
        ), patch("app.repositories.price_repo.save_price_snapshot", side_effect=blocking_save):
            req = asyncio.create_task(self.cache.get("sm-001", "Phone"))
            await ready_async.wait()
            self.assertTrue(db_started.is_set())

            req.cancel()
            await asyncio.sleep(0.01)
            self.assertFalse(req.done(), "Must drain active parent DB worker session before completing cancel")

            db_release.set()
            with self.assertRaises(asyncio.CancelledError):
                await req

            self.assertTrue(db_closed.is_set())
            self.assertFalse(self.cache._inflight)
            self.assertFalse(self.cache._cache)


class TestPriceEndpoint(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(prices, "price_cache"), "Endpoint cache wrapper is missing")
        self.service = importlib.import_module("app.price_service")
        self.sw = load_scrape_worker(self)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        test_cache = self.service.PriceCache()
        self.addCleanup(lambda: asyncio.run(test_cache.aclose(timeout=1.0)))
        self.stack.enter_context(patch.object(prices, "price_cache", test_cache))
        self.session = MagicMock()
        self.stack.enter_context(patch.object(prices.catalog_repo, "get_product_by_id", return_value=None))
        self.stack.enter_context(patch("app.repositories.price_repo.save_price_snapshot", return_value=False))

        def session_dependency():
            try:
                yield self.session
            finally:
                self.session.close()

        app.dependency_overrides[get_db] = session_dependency
        self.addCleanup(app.dependency_overrides.pop, get_db, None)
        app.dependency_overrides[check_price_rate_limit] = lambda: "testclient"
        self.addCleanup(app.dependency_overrides.pop, check_price_rate_limit, None)
        price_rate_limiter.reset()
        self.addCleanup(price_rate_limiter.reset)
        self.client = TestClient(app)

    def test_session_closed_before_scrape_and_api_cache_contract(self):
        async def fetch(product_id, name, **kwargs):
            self.session.close.assert_called()
            return worker_outcome(self.sw)

        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=fetch)) as fetch_mock:
            first = self.client.get("/api/prices/sm-001")
            second = self.client.get("/api/prices/sm-001")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(set(first.json()), {"product_id", "product_name", "prices", "last_updated"})
        fetch_mock.assert_awaited_once()

    def test_lookup_runs_in_worker_and_failure_retains_fallback(self):
        request_thread = None

        async def fetch(*args, **kwargs):
            nonlocal request_thread
            request_thread = threading.get_ident()
            return worker_outcome(self.sw)

        lookup_threads = []

        def lookup(*args):
            lookup_threads.append(threading.get_ident())
            raise RuntimeError("DB unavailable")

        with patch.object(prices.catalog_repo, "get_product_by_id", side_effect=lookup), patch.object(
            self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=fetch)
        ):
            self.assertEqual(self.client.get("/api/prices/sm-001").status_code, 200)
        self.assertNotEqual(lookup_threads, [request_thread])
        self.session.close.assert_called()

    def test_unknown_id_still_404_without_scraping(self):
        with patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock()) as fetch:
            result = self.client.get("/api/prices/missing")
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.json(), {"detail": "Product not found"})
        self.assertFalse(prices.price_cache._cache)
        self.session.close.assert_called()
        fetch.assert_not_called()

    def test_unexpected_error_still_500_and_closes_session(self):
        with patch.object(
            self.sw,
            "run_isolated_scrape_flight",
            AsyncMock(side_effect=self.sw.ScrapeWorkerError("boom")),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            self.assertEqual(client.get("/api/prices/sm-001").status_code, 500)
        self.session.close.assert_called()
        self.assertFalse(prices.price_cache._inflight)

    def test_deadline_returns_504_and_releases_lookup_session(self):
        """Updated for approved D7: total flight deadline returns HTTP 504 error, 0 cache, 0 DB persistence."""
        async def timeout_after_lookup(*args, **kwargs):
            self.session.close.assert_called()
            raise self.sw.ScrapeTimeoutError(
                "Marketplace price lookup timed out",
                budget=35.0,
                elapsed=33.01,
                worker_pid=12345,
                exitcode=1,
                worker_stopped=True,
                reaped=True,
                within_budget=True,
            )

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=timeout_after_lookup))
            )
            save = stack.enter_context(patch("app.repositories.price_repo.save_price_snapshot", return_value=True))
            result = self.client.get("/api/prices/sm-001")
        self.assertEqual(result.status_code, 504)
        self.assertEqual(result.json(), {"detail": "Marketplace price lookup timed out"})
        self.assertFalse(prices.price_cache._inflight)
        self.assertFalse(prices.price_cache._cache)
        save.assert_not_called()

    def test_t14_api_contracts_and_separate_scrape_vs_endpoint_latency(self):
        """T-14: Verify 200 scraped, 200 individual fallback, 404, 504 timeout, 500 crash, and separate latencies."""
        scrape_durations = []

        def slow_lookup(*args):
            time.sleep(0.03)
            return None

        async def fast_partial_worker(product_id, name, **kwargs):
            t_s = time.monotonic()
            await asyncio.sleep(0.01)
            scrape_durations.append(time.monotonic() - t_s)
            return worker_outcome(self.sw, offers=[scraped_offer(marketplace="Tokopedia", price=19_200_000)])

        with patch.object(prices.catalog_repo, "get_product_by_id", side_effect=slow_lookup), patch.object(
            self.sw, "run_isolated_scrape_flight", AsyncMock(side_effect=fast_partial_worker)
        ), patch("app.repositories.price_repo.save_price_snapshot", return_value=True) as save:
            t_ep = time.monotonic()
            resp = self.client.get("/api/prices/sm-001")
            endpoint_elapsed = time.monotonic() - t_ep

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(set(body.keys()), {"product_id", "product_name", "prices", "last_updated"})
        self.assertEqual({p["marketplace"]: p["source"] for p in body["prices"]},
                         {"Tokopedia": "scraped", "Shopee": "fallback", "Lazada": "fallback"})
        self.assertEqual(save.call_count, 3)
        # Endpoint latency includes DB lookup + persistence outside worker budget (D6)
        self.assertGreater(endpoint_elapsed, scrape_durations[0])


class TestScrapeResources(unittest.IsolatedAsyncioTestCase):
    async def test_deadline_must_drain_an_already_running_parser(self):
        """T-04: Characterizes why in-process parser threads stay alive past deadline and cannot claim hard-stop."""
        ready = asyncio.Event()
        release = threading.Event()
        parser_alive = threading.Event()
        loop = asyncio.get_running_loop()

        def parse(*args):
            parser_alive.set()
            loop.call_soon_threadsafe(ready.set)
            try:
                release.wait(2)
                return None
            finally:
                parser_alive.clear()

        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = httpx.Response(200, text="HTML")
        with patch.object(scraper.httpx, "AsyncClient", return_value=client), \
             patch.object(scraper, "_parse_listing", side_effect=parse), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)), \
             patch.object(scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", .01), \
             patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
            task = asyncio.create_task(scraper.get_live_prices("sm-001", "Phone"))
            await ready.wait()
            try:
                await asyncio.sleep(.03)
                self.assertTrue(parser_alive.is_set(), "Thread parser remains active after coroutine deadline")
                self.assertFalse(task.done(), "A deadline cannot safely terminate a parser thread")
            finally:
                release.set()
                result = await asyncio.wait_for(task, 1)
            self.assertEqual(len(result.prices), 3)
            client.__aexit__.assert_awaited_once()

    async def test_cancellation_during_deadline_cleanup_is_propagated(self):
        cleaning, release = asyncio.Event(), asyncio.Event()
        active = set()

        async def fetch(*args):
            task = asyncio.current_task()
            active.add(task)
            try:
                await asyncio.Event().wait()
            finally:
                cleaning.set()
                await release.wait()
                active.remove(task)

        with ExitStack() as stack:
            mocks = mock_marketplaces(stack)
            for mock in mocks:
                mock.side_effect = fetch
            stack.enter_context(patch.object(scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", .02))
            save = stack.enter_context(patch("app.repositories.price_repo.save_price_snapshot"))
            task = asyncio.create_task(scraper.get_live_prices("sm-001", "Phone"))
            await cleaning.wait()
            task.cancel()
            await asyncio.sleep(0)
            task.cancel()
            await asyncio.sleep(0)
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertFalse(active)
            save.assert_not_called()

    async def test_parser_cancellation_drains_worker_and_closes_client(self):
        ready = asyncio.Event()
        release, closed = threading.Event(), threading.Event()
        loop = asyncio.get_running_loop()

        def parse(*args):
            loop.call_soon_threadsafe(ready.set)
            try:
                release.wait(2)
                return None
            finally:
                closed.set()

        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = httpx.Response(200, text="HTML")
        with patch.object(scraper.httpx, "AsyncClient", return_value=client), \
             patch.object(scraper, "_parse_listing", side_effect=parse):
            task = asyncio.create_task(scraper._scrape_tokopedia("Phone"))
            await ready.wait()
            task.cancel()
            await asyncio.sleep(0)
            self.assertFalse(task.done())
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertTrue(closed.is_set())
            client.__aexit__.assert_awaited_once()

    async def test_cancellation_waits_for_snapshot_session_cleanup(self):
        started, release, closed = threading.Event(), threading.Event(), threading.Event()
        loop = asyncio.get_running_loop()
        ready = asyncio.Event()

        def save(**kwargs):
            started.set()
            loop.call_soon_threadsafe(ready.set)
            try:
                release.wait(2)
            finally:
                closed.set()
            return True

        with ExitStack() as stack:
            mock_marketplaces(stack)
            stack.enter_context(patch("app.repositories.price_repo.save_price_snapshot", side_effect=save))
            task = asyncio.create_task(scraper.get_live_prices("sm-001", "Phone"))
            await ready.wait()
            self.assertTrue(started.is_set())
            task.cancel()
            await asyncio.sleep(0)
            self.assertFalse(task.done(), "Cancellation must drain the active DB worker")
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertTrue(closed.is_set())

    async def test_individual_timeouts_unchanged_and_clients_closed(self):
        clients = []

        class Client:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.closed = False
                clients.append(self)

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                self.closed = True

            async def get(self, url):
                raise httpx.ReadTimeout("test")

        with patch.object(scraper.httpx, "AsyncClient", Client), \
             patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
            result = await scraper.get_live_prices("sm-001", "Phone")
        self.assertTrue(all(p.source == "fallback" for p in result.prices))
        self.assertEqual(len(clients), 3)
        self.assertTrue(all(client.closed for client in clients))
        self.assertTrue(all(client.kwargs["timeout"] is scraper.TIMEOUT for client in clients))
        self.assertEqual(scraper.TIMEOUT.as_dict(), {"connect": 5, "read": 10, "write": 10, "pool": 10})
        self.assertEqual(scraper.TOTAL_SCRAPE_TIMEOUT_SECONDS, 35)

    async def test_html_parsing_and_persistence_do_not_block_loop(self):
        loop_thread = threading.get_ident()
        parse_threads, save_threads = [], []
        original = scraper.BeautifulSoup

        def parse(*args):
            parse_threads.append(threading.get_ident())
            time.sleep(.02)
            return original(*args)

        def save(**kwargs):
            save_threads.append(threading.get_ident())
            time.sleep(.01)
            return True

        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = httpx.Response(200, text='<div class="shopee-price">Rp 100.000</div>')
        with patch.object(scraper.httpx, "AsyncClient", return_value=client), \
             patch.object(scraper, "BeautifulSoup", side_effect=parse), \
             patch("app.repositories.price_repo.save_price_snapshot", side_effect=save):
            await scraper.get_live_prices("sm-001", "Phone")
        self.assertEqual(len(parse_threads), 3)
        self.assertEqual(len(save_threads), 3)
        self.assertNotIn(loop_thread, parse_threads + save_threads)

    async def test_total_deadline_closes_http_clients(self):
        self.assertTrue(hasattr(scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS"), "Total deadline missing")
        clients = []

        class Client:
            async def __aenter__(self):
                self.closed = False
                clients.append(self)
                return self

            async def __aexit__(self, *args):
                self.closed = True

            async def get(self, url):
                await asyncio.Event().wait()

        with patch.object(scraper.httpx, "AsyncClient", side_effect=lambda **kw: Client()), \
             patch.object(scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", .02), \
             patch("app.repositories.price_repo.save_price_snapshot", return_value=True):
            result = await asyncio.wait_for(scraper.get_live_prices("sm-001", "Phone"), 1)
        self.assertEqual(len(clients), 3)
        self.assertTrue(all(client.closed for client in clients))
        self.assertTrue(all(p.source == "fallback" for p in result.prices))


class TestDatabaseSafetyGuard(unittest.TestCase):
    """T-17: Pre-import guard prevents dev DB opens/writes and never leaks secrets in errors."""

    def test_t17_missing_db_url_disables_dev_engine_before_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            dotenv_file = Path(tmp) / ".env"
            dotenv_file.write_text(
                "DATABASE_URL=postgresql://postgres:TOP_SECRET_123@localhost:5432/comparebuy\n",
                encoding="utf-8",
            )
            env = {}
            enforce_safe_test_db_env(env=env, dotenv_path=dotenv_file)
            self.assertEqual(env["DATABASE_URL"], "")

    def test_t17_dev_database_url_fails_closed_without_leaking_secret(self):
        secret = "ULTRA_SECRET_DEV_PW_999"
        with tempfile.TemporaryDirectory() as tmp:
            dotenv_file = Path(tmp) / ".env"
            dotenv_file.write_text(
                f"DATABASE_URL=postgresql://postgres:{secret}@localhost:5432/comparebuy\n",
                encoding="utf-8",
            )
            env = {"DATABASE_URL": f"postgresql://postgres:{secret}@localhost:5432/comparebuy"}
            with self.assertRaises(RuntimeError) as ctx:
                enforce_safe_test_db_env(env=env, dotenv_path=dotenv_file)
            self.assertNotIn(secret, str(ctx.exception))

            # Also verify TEST_DATABASE_URL pointing to dev DB fails closed without leaking secret
            env2 = {"TEST_DATABASE_URL": f"postgresql://postgres:{secret}@localhost:5432/comparebuy"}
            with self.assertRaises(RuntimeError) as ctx2:
                enforce_safe_test_db_env(env=env2, dotenv_path=dotenv_file)
            self.assertNotIn(secret, str(ctx2.exception))

    def test_t17_subprocess_import_tests_package_disables_dev_engine(self):
        backend_dir = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env.pop("DATABASE_URL", None)
        env.pop("TEST_DATABASE_URL", None)
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import tests, app.db as db; assert db.engine is None and db.SessionLocal is None; print('GUARD_SUBPROCESS_OK')",
            ],
            cwd=str(backend_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("GUARD_SUBPROCESS_OK", proc.stdout)

    def test_f06_db_guard_enforced_on_module_and_direct_file_execution_of_test_scrape_worker(self):
        """F06-01 & F06-02: Both `python -m unittest` and `python tests/test_scrape_worker.py` enforce _db_guard."""
        backend_dir = Path(__file__).resolve().parent.parent
        secret = "SUPER_SECRET_DEV_PW_F06"
        unsafe_url = f"postgresql://postgres:{secret}@localhost:5432/comparebuy"

        for cmd in (
            [sys.executable, "-m", "unittest", "tests.test_scrape_worker.TestScrapeWorkerHardening.test_f01_max_concurrent_env_validation"],
            [sys.executable, "tests/test_scrape_worker.py", "TestScrapeWorkerHardening.test_f01_max_concurrent_env_validation"],
        ):
            env_bad = os.environ.copy()
            env_bad["DATABASE_URL"] = unsafe_url
            env_bad.pop("TEST_DATABASE_URL", None)
            proc_bad = subprocess.run(
                cmd,
                cwd=str(backend_dir),
                env=env_bad,
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertNotEqual(proc_bad.returncode, 0, msg=f"Unsafe DB URL must fail closed for {cmd}")
            combined = (proc_bad.stdout or "") + "\n" + (proc_bad.stderr or "")
            self.assertIn("Unsafe DATABASE_URL rejected", combined)
            self.assertNotIn(secret, combined)

        # Direct execution with DATABASE_URL unset must disable dev engine and pass cleanly
        env_safe = os.environ.copy()
        env_safe.pop("DATABASE_URL", None)
        env_safe.pop("TEST_DATABASE_URL", None)
        proc_ok = subprocess.run(
            [
                sys.executable,
                "tests/test_scrape_worker.py",
                "TestScrapeWorkerHardening.test_f01_max_concurrent_env_validation",
            ],
            cwd=str(backend_dir),
            env=env_safe,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc_ok.returncode, 0, msg=proc_ok.stderr)


class TestPreProductionHardening(unittest.IsolatedAsyncioTestCase):
    """SEC-008 Pre-Production Hardening unit & endpoint tests for F-01, F-02, F-04, F-07, and F-08."""

    async def asyncSetUp(self):
        self.service = importlib.import_module("app.price_service")
        self.sw = load_scrape_worker(self)
        price_rate_limiter.reset()

    async def asyncTearDown(self):
        price_rate_limiter.reset()

    async def _close_if_supported(self, cache) -> None:
        if hasattr(cache, "aclose"):
            await cache.aclose(timeout=1.0)

    async def test_f01_cancelled_waiter_holds_admission_slot_until_worker_actually_stops(self):
        """F01-04: Waiter cancellation must NOT free admission slot while worker teardown is still active."""
        started = asyncio.Event()
        teardown_entered = asyncio.Event()
        allow_worker_exit = asyncio.Event()

        async def slow_stop_worker(product_id, name, *, cancel_event=None, **kwargs):
            if product_id == "sm-001":
                started.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    teardown_entered.set()
                    await allow_worker_exit.wait()
            return worker_outcome(self.sw, offers=[scraped_offer(price=18_222_000)])

        cache = self.service.PriceCache(max_concurrent=1)
        try:
            with patch.object(self.sw, "run_isolated_scrape_flight", side_effect=slow_stop_worker), patch(
                "app.repositories.price_repo.save_price_snapshot", return_value=False
            ):
                w1 = asyncio.create_task(cache.get("sm-001", "Phone"))
                await started.wait()
                w1.cancel()
                await teardown_entered.wait()

                # Worker teardown is still in progress (`allow_worker_exit` is unset) -> slot 1/1 MUST stay held!
                with self.assertRaises(self.sw.ScrapeOverloadError):
                    await cache.get("sm-002", "Other")

                # Once worker actually finishes stopping, slot 1/1 is released and sm-002 succeeds!
                allow_worker_exit.set()
                with self.assertRaises(asyncio.CancelledError):
                    await w1

                ok = await cache.get("sm-002", "Other")
                self.assertEqual(ok.product_id, "sm-002")
                self.assertEqual(ok.prices[0].price, 18_222_000)
        finally:
            await self._close_if_supported(cache)

    def test_f01_api_overload_returns_503_without_affecting_200_404_504_500(self):
        """F-01 API contract: ScrapeOverloadError -> 503; 200/404/504/500 contracts remain unchanged."""
        self.assertTrue(hasattr(self.sw, "ScrapeOverloadError"))
        cache = self.service.PriceCache(max_concurrent=1)

        def no_db():
            yield None

        app.dependency_overrides[get_db] = no_db
        app.dependency_overrides[check_price_rate_limit] = lambda: "testclient"
        try:
            with patch.object(prices, "price_cache", cache), patch(
                "app.repositories.price_repo.save_price_snapshot", return_value=False
            ):
                # 1) Overload -> 503 (never 504!)
                with patch.object(
                    cache,
                    "get",
                    AsyncMock(side_effect=self.sw.ScrapeOverloadError("Marketplace price lookup busy")),
                ):
                    client = TestClient(app, raise_server_exceptions=False)
                    r503 = client.get("/api/prices/sm-001")
                    self.assertEqual(r503.status_code, 503)
                    self.assertEqual(r503.json(), {"detail": "Marketplace price lookup busy"})

                # 2) Unknown product -> 404 without hitting cache
                r404 = TestClient(app).get("/api/prices/not-a-real-sku")
                self.assertEqual(r404.status_code, 404)

                # 3) Timeout -> 504
                with patch.object(
                    self.sw,
                    "run_isolated_scrape_flight",
                    AsyncMock(side_effect=self.sw.ScrapeTimeoutError("Marketplace price lookup timed out")),
                ):
                    r504 = TestClient(app).get("/api/prices/sm-001")
                    self.assertEqual(r504.status_code, 504)

                # 4) Worker crash -> 500
                with patch.object(
                    self.sw,
                    "run_isolated_scrape_flight",
                    AsyncMock(side_effect=self.sw.ScrapeWorkerError("worker boom")),
                ):
                    r500 = TestClient(app, raise_server_exceptions=False).get("/api/prices/sm-001")
                    self.assertEqual(r500.status_code, 500)

                # 5) Normal -> 200
                with patch.object(
                    self.sw,
                    "run_isolated_scrape_flight",
                    AsyncMock(return_value=worker_outcome(self.sw)),
                ):
                    r200 = TestClient(app).get("/api/prices/sm-001")
                    self.assertEqual(r200.status_code, 200)
        finally:
            app.dependency_overrides.pop(check_price_rate_limit, None)
            app.dependency_overrides.pop(get_db, None)
            if hasattr(cache, "aclose"):
                asyncio.run(cache.aclose(timeout=1.0))

    async def test_f02_terminate_and_kill_failure_quarantines_flight_blocks_duplicate_and_recovers(self):
        """F02-01..03: Simulated terminate+kill failure holds QUARANTINED flight & slot until worker exits."""
        import inspect

        spawn_count = 0

        class FakeUnkillableProcess:
            def __init__(self, target=None, args=(), daemon=True):
                nonlocal spawn_count
                spawn_count += 1
                self.pid = 88000 + spawn_count
                self.exitcode = None
                self.sentinel = object()
                self.terminate_called = 0
                self.kill_called = 0
                self.closed = False
                self._alive = True

            def start(self):
                pass

            def is_alive(self):
                return self._alive

            def terminate(self):
                self.terminate_called += 1
                raise PermissionError("simulated OS terminate failure")

            def kill(self):
                self.kill_called += 1
                raise PermissionError("simulated OS kill failure")

            def join(self, timeout=None):
                pass

            def close(self):
                self.closed = True

        fake_proc_holder: list[FakeUnkillableProcess] = []

        def make_proc(*args, **kwargs):
            p = FakeUnkillableProcess(*args, **kwargs)
            fake_proc_holder.append(p)
            return p

        class DummyConn:
            def poll(self, timeout=0):
                return False

            def close(self):
                pass

        ctor_kwargs = {"max_concurrent": 1} if "max_concurrent" in inspect.signature(self.service.PriceCache).parameters else {}
        cache = self.service.PriceCache(**ctor_kwargs)
        try:
            with patch.object(self.sw._MP_CTX, "Pipe", return_value=(DummyConn(), DummyConn())), patch.object(
                self.sw._MP_CTX, "Process", side_effect=make_proc
            ), patch.object(self.sw.multiprocessing.connection, "wait", side_effect=lambda h, timeout=0: time.sleep(min(timeout or 0, 0.01))), patch.object(
                scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", 0.08
            ), patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
                # 1) First request times out -> terminate() & kill() both fail -> ScrapeWorkerCleanupError!
                with self.assertRaises(self.sw.ScrapeWorkerCleanupError):
                    await cache.get("sm-001", "Phone")

                self.assertEqual(spawn_count, 1)
                proc1 = fake_proc_holder[0]
                self.assertGreaterEqual(proc1.terminate_called, 1)
                self.assertGreaterEqual(proc1.kill_called, 1)

                # Flight MUST be QUARANTINED (not STOPPED), still in _inflight, and still holding slot 1/1!
                self.assertIn(("sm-001", "Phone"), cache._inflight)
                self.assertEqual(cache._inflight[("sm-001", "Phone")].state, "QUARANTINED")

                # 2) Replacement request for sm-001 MUST NOT spawn a duplicate worker while proc1 is alive!
                with self.assertRaises(self.sw.ScrapeWorkerCleanupError):
                    await cache.get("sm-001", "Phone")
                self.assertEqual(spawn_count, 1, "No duplicate worker may spawn while old worker is unconfirmed")

                # 3) Distinct key sm-002 sees the 1/1 admission slot still occupied by quarantined proc1!
                with self.assertRaises(self.sw.ScrapeOverloadError):
                    await cache.get("sm-002", "Other")
                self.assertEqual(spawn_count, 1)

                # 4) Once OS finally confirms proc1 exited, recovery reaps proc1, frees slot, and allows new flight!
                proc1._alive = False
                proc1.exitcode = -9

            with patch.object(
                self.sw,
                "run_isolated_scrape_flight",
                AsyncMock(return_value=worker_outcome(self.sw, offers=[scraped_offer(price=17_999_000)])),
            ), patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
                recovered = await cache.get("sm-001", "Phone")
                self.assertTrue(proc1.closed)
                self.assertEqual(recovered.prices[0].price, 17_999_000)
                self.assertFalse(cache._inflight)
        finally:
            await self._close_if_supported(cache)

    async def test_f02_last_waiter_cancel_cleanup_failure_quarantines_instead_of_swallowing(self):
        """F02-01 & F02-02: Cleanup failure during last-waiter cancellation must quarantine flight, not release it."""
        import inspect

        class AliveStubProc:
            pid = 91919
            exitcode = None
            closed = False

            def is_alive(self):
                return self.exitcode is None

            def join(self, timeout=None):
                pass

            def close(self):
                self.closed = True

        stub = AliveStubProc()
        entered = asyncio.Event()
        loop = asyncio.get_running_loop()

        def sync_supervisor_fail_on_cancel(*args, cancel_event=None, on_stopping=None, **kwargs):
            loop.call_soon_threadsafe(entered.set)
            while not cancel_event.is_set():
                time.sleep(0.005)
            if on_stopping is not None:
                on_stopping()
            err = self.sw.ScrapeWorkerCleanupError("cancel cleanup failed")
            err.worker_pid = stub.pid
            err.unreaped_proc = stub
            raise err

        ctor_kwargs = {"max_concurrent": 1} if "max_concurrent" in inspect.signature(self.service.PriceCache).parameters else {}
        cache = self.service.PriceCache(**ctor_kwargs)
        try:
            with patch.object(self.sw, "_supervise_worker_sync", side_effect=sync_supervisor_fail_on_cancel):
                req = asyncio.create_task(cache.get("sm-001", "Phone"))
                await entered.wait()
                req.cancel()
                with self.assertRaises((asyncio.CancelledError, self.sw.ScrapeWorkerCleanupError)):
                    await req

                # Crucial: flight MUST be QUARANTINED and hold its slot because worker never confirmed stop!
                self.assertIn(("sm-001", "Phone"), cache._inflight)
                self.assertEqual(cache._inflight[("sm-001", "Phone")].state, "QUARANTINED")
                with self.assertRaises(self.sw.ScrapeWorkerCleanupError):
                    await cache.get("sm-001", "Phone")

                stub.exitcode = -9
        finally:
            await self._close_if_supported(cache)

    async def test_f04_timeout_waiting_on_stopping_flight_maps_to_scrape_timeout_504(self):
        """F04-01 & F04-02: Waiting on STOPPING past bound raises ScrapeTimeoutError -> HTTP 504 (DB error untouched)."""
        in_stopping = asyncio.Event()
        release_stopping = asyncio.Event()

        async def stuck_stopping(*args, **kwargs):
            try:
                await asyncio.Event().wait()
            finally:
                in_stopping.set()
                await release_stopping.wait()

        cache = self.service.PriceCache()
        try:
            with patch.object(self.sw, "run_isolated_scrape_flight", side_effect=stuck_stopping), patch.object(
                scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", 0.05
            ):
                r1 = asyncio.create_task(cache.get("sm-001", "Samsung Galaxy S24 Ultra"))
                await asyncio.sleep(0.01)
                r1.cancel()
                await in_stopping.wait()

                # Replacement call times out waiting on STOPPING -> MUST raise ScrapeTimeoutError, not bare TimeoutError
                with self.assertRaises(self.sw.ScrapeTimeoutError):
                    await cache.get("sm-001", "Samsung Galaxy S24 Ultra")

                # Router mapping check: GET /api/prices/sm-001 -> HTTP 504
                def no_db():
                    yield None

                app.dependency_overrides[get_db] = no_db
                app.dependency_overrides[check_price_rate_limit] = lambda: "testclient"
                try:
                    with patch.object(prices, "price_cache", cache):
                        async with httpx.AsyncClient(
                            transport=httpx.ASGITransport(app=app), base_url="http://test"
                        ) as aclient:
                            resp = await aclient.get("/api/prices/sm-001")
                        self.assertEqual(resp.status_code, 504)
                        self.assertEqual(resp.json(), {"detail": "Marketplace price lookup timed out"})
                finally:
                    app.dependency_overrides.pop(check_price_rate_limit, None)
                    app.dependency_overrides.pop(get_db, None)

                release_stopping.set()
                await asyncio.gather(r1, return_exceptions=True)

            # Verify DB TimeoutError in get_price_product_name is NOT mis-mapped to 504 (falls back to memory catalog)
            def db_with_timeout():
                s = MagicMock()
                yield s

            app.dependency_overrides[get_db] = db_with_timeout
            app.dependency_overrides[check_price_rate_limit] = lambda: "testclient"
            try:
                with patch.object(prices, "price_cache", cache), patch.object(
                    prices.catalog_repo, "get_product_by_id", side_effect=TimeoutError("DB query timeout")
                ), patch.object(
                    self.sw, "run_isolated_scrape_flight", AsyncMock(return_value=worker_outcome(self.sw))
                ), patch("app.repositories.price_repo.save_price_snapshot", return_value=False):
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app), base_url="http://test"
                    ) as aclient_db:
                        resp_db = await aclient_db.get("/api/prices/sm-001")
                    self.assertEqual(resp_db.status_code, 200)
            finally:
                app.dependency_overrides.pop(check_price_rate_limit, None)
                app.dependency_overrides.pop(get_db, None)
        finally:
            await self._close_if_supported(cache)

    async def test_f07_same_tick_last_waiter_cancel_and_task_failure_emits_no_unretrieved_warning(self):
        """F07-01 & F07-02: Same-tick sole-waiter cancel + task failure emits 0 unretrieved-exception logs."""
        import gc

        loop = asyncio.get_running_loop()
        unhandled_contexts: list[dict] = []
        prev_handler = loop.get_exception_handler()
        loop.set_exception_handler(lambda _loop, ctx: unhandled_contexts.append(ctx))

        fail_gate = asyncio.Future()

        async def fail_when_triggered(*args, **kwargs):
            await fail_gate
            raise self.sw.ScrapeWorkerError("simultaneous worker failure")

        cache = self.service.PriceCache()
        try:
            with patch.object(self.sw, "run_isolated_scrape_flight", side_effect=fail_when_triggered):
                waiter = asyncio.create_task(cache.get("sm-001", "Phone"))
                await asyncio.sleep(0.01)
                flight_ref = cache._inflight[("sm-001", "Phone")]

                # Simulate multi-waiter race: w1 cancels (shield removes _inner_done_callback while waiters > 0
                # skips _drain_task), and flight.task fails on the next step with zero remaining observers!
                flight_ref.waiters += 1
                waiter.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await waiter
                flight_ref.waiters -= 1
                fail_gate.set_result(True)
                await asyncio.sleep(0.01)
                del flight_ref

            await asyncio.sleep(0.01)
            gc.collect()
            await asyncio.sleep(0)

            unretrieved = [
                ctx for ctx in unhandled_contexts if "Task exception was never retrieved" in ctx.get("message", "")
            ]
            self.assertEqual(unretrieved, [], f"Unexpected unretrieved task exception contexts: {unretrieved}")

            # Also verify normal awaiting caller still receives the exact ScrapeWorkerError + message!
            with patch.object(
                self.sw,
                "run_isolated_scrape_flight",
                AsyncMock(side_effect=self.sw.ScrapeWorkerError("boom-observable")),
            ):
                with self.assertRaisesRegex(self.sw.ScrapeWorkerError, "boom-observable"):
                    await cache.get("sm-002", "Other")
        finally:
            loop.set_exception_handler(prev_handler)
            await self._close_if_supported(cache)

    async def test_f08_unused_generation_field_removed_and_identity_guard_intact(self):
        """F08-01 & F08-02: _Flight.generation and _next_generation removed; object identity guard preserved."""
        self.assertNotIn("generation", self.service._Flight.__dataclass_fields__)
        cache = self.service.PriceCache()
        self.assertFalse(hasattr(cache, "_next_generation"))
        await self._close_if_supported(cache)


if __name__ == "__main__":
    unittest.main()
