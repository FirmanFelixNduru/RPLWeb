"""SEC-008 persistence checks on the guarded, rollback-only PostgreSQL fixture (includes T-12)."""
import importlib
import importlib.util
from pathlib import Path
import tempfile
import time
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests._db_guard import empty_scrape_worker, enforce_safe_test_db_env
from tests.test_scrape_worker import is_os_pid_running

enforce_safe_test_db_env()

from app import scraper
from app.db import get_db
from app.entities import MarketplacePrice
from app.main import app
from app.repositories import price_repo
from app.routers import prices
from tests import test_catalog as catalog_tests

setUpModule = catalog_tests.setUpModule
tearDownModule = catalog_tests.tearDownModule


def pg_hang_and_attempt_late_offer_worker(product_id: str, product_name: str) -> list[dict]:
    """Writes child PID to marker file if present, hangs past flight budget, then returns fake offer."""
    marker = os.environ.get("COMPAREBUY_T12_PID_FILE", "")
    if marker and Path(marker).exists():
        Path(marker).write_text(str(os.getpid()), encoding="utf-8")
    time.sleep(30.0)
    return [
        {
            "marketplace": "Tokopedia",
            "price": 18_000_000,
            "url": "https://www.tokopedia.com/search?q=pgt-001",
            "seller": "ShouldNeverPersist",
            "available": True,
            "captured_at": "2026-11-07T00:00:00+00:00",
        }
    ]


import os  # noqa: E402


class TestPricePostgres(catalog_tests.PostgresCatalogTestCase):
    def test_fallback_rows_cache_and_short_sessions(self):
        self.assertTrue(hasattr(prices, "price_cache"), "Endpoint cache wrapper missing")
        self.assertIsNotNone(
            importlib.util.find_spec("app.scrape_worker"),
            "SEC-008 AC-08 worker module app.scrape_worker is missing",
        )
        service = importlib.import_module("app.price_service")
        sw = importlib.import_module("app.scrape_worker")
        active = set()
        sessions = []

        def factory():
            session = Session(bind=self.connection, join_transaction_mode="create_savepoint")
            sessions.append(session)
            active.add(id(session))
            close = session.close

            def close_session():
                try:
                    close()
                finally:
                    active.discard(id(session))

            session.close = close_session
            return session

        def lookup_session():
            db = factory()
            try:
                yield db
            finally:
                db.close()

        orig_run = sw.run_isolated_scrape_flight

        async def checked_run_isolated(*args, **kwargs):
            self.assertFalse(active, "Lookup session was held during external scraping")
            return await orig_run(*args, **kwargs)

        app.dependency_overrides[get_db] = lookup_session
        try:
            with ExitStack() as stack:
                stack.enter_context(
                    patch.object(prices, "price_cache", service.PriceCache(worker_fn=empty_scrape_worker))
                )
                stack.enter_context(patch.object(price_repo, "SessionLocal", side_effect=factory))
                stack.enter_context(
                    patch.dict(scraper.FALLBACK_PRICES, {"pgt-001": scraper.FALLBACK_PRICES["sm-001"]})
                )
                stack.enter_context(
                    patch.object(sw, "run_isolated_scrape_flight", side_effect=checked_run_isolated)
                )
                with TestClient(app) as client:
                    first = client.get("/api/prices/pgt-001")
                    second = client.get("/api/prices/pgt-001")
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.json(), second.json())
            self.assertFalse(active)
            self.assertEqual(len(sessions), 5)  # Two lookups, three snapshot sessions.
            rows = self.session.query(MarketplacePrice).filter_by(product_id="pgt-001").all()
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(row.source == "fallback" and row.captured_at for row in rows))
            self.assertTrue(all(p["captured_at"] is None for p in first.json()["prices"]))
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_snapshot_error_rolls_back_and_closes_session(self):
        db = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        with patch.object(price_repo, "SessionLocal", return_value=db), \
             patch.object(db, "commit", side_effect=RuntimeError("commit failed")), \
             patch.object(db, "rollback", wraps=db.rollback) as rollback, \
             patch.object(db, "close", wraps=db.close) as close:
            saved = price_repo.save_price_snapshot("pgt-001", "tokopedia", 100000,
                                                   "Seller", "https://tokopedia.com/test")
            self.assertFalse(saved)
            rollback.assert_called_once()
            close.assert_called_once()
        self.assertEqual(self.session.query(MarketplacePrice).filter_by(product_id="pgt-001").count(), 0)

    def test_t12_total_timeout_persists_zero_rows_while_normal_fallback_persists_three(self):
        """T-12: Total-timeout flight writes 0 DB rows (even after worker death); normal fallback writes 3."""
        self.assertIsNotNone(
            importlib.util.find_spec("app.scrape_worker"),
            "SEC-008 AC-08 worker module app.scrape_worker is missing",
        )
        service = importlib.import_module("app.price_service")
        sessions_opened = []

        def factory():
            session = Session(bind=self.connection, join_transaction_mode="create_savepoint")
            sessions_opened.append(session)
            return session

        def lookup_session():
            db = factory()
            try:
                yield db
            finally:
                db.close()

        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            pid_file = tf.name

        app.dependency_overrides[get_db] = lookup_session
        try:
            # Part A: Total-timeout flight for pgt-001 -> HTTP 504, 0 snapshot sessions, 0 DB rows
            with ExitStack() as stack:
                stack.enter_context(patch.dict(os.environ, {"COMPAREBUY_T12_PID_FILE": pid_file}))
                stack.enter_context(
                    patch.object(
                        prices,
                        "price_cache",
                        service.PriceCache(worker_fn=pg_hang_and_attempt_late_offer_worker),
                    )
                )
                stack.enter_context(patch.object(scraper, "TOTAL_SCRAPE_TIMEOUT_SECONDS", 1.8))
                stack.enter_context(patch.object(price_repo, "SessionLocal", side_effect=factory))
                stack.enter_context(
                    patch.dict(
                        scraper.FALLBACK_PRICES,
                        {
                            "pgt-001": scraper.FALLBACK_PRICES["sm-001"],
                            "pgt-002": scraper.FALLBACK_PRICES["sm-002"],
                        },
                    )
                )
                with TestClient(app) as client:
                    timeout_resp = client.get("/api/prices/pgt-001")
                    self.assertEqual(timeout_resp.status_code, 504)
                    self.assertEqual(timeout_resp.json(), {"detail": "Marketplace price lookup timed out"})
                    # Only 1 session opened (the lookup session), 0 snapshot sessions
                    self.assertEqual(len(sessions_opened), 1)
                    self.assertEqual(
                        self.session.query(MarketplacePrice).filter_by(product_id="pgt-001").count(),
                        0,
                    )
                    # Confirm worker process is dead at OS level and still 0 delayed writes
                    pid_txt = Path(pid_file).read_text(encoding="utf-8").strip()
                    if pid_txt:
                        self.assertFalse(is_os_pid_running(int(pid_txt)))
                    self.assertEqual(
                        self.session.query(MarketplacePrice).filter_by(product_id="pgt-001").count(),
                        0,
                    )
                    self.assertFalse(prices.price_cache._cache)

                    # Part B: Normal individual failure fallback for pgt-002 -> HTTP 200 and 3 fallback rows
                    prices.price_cache._worker_fn = empty_scrape_worker
                    ok_resp = client.get("/api/prices/pgt-002")
                    self.assertEqual(ok_resp.status_code, 200)
                    rows_pgt2 = self.session.query(MarketplacePrice).filter_by(product_id="pgt-002").all()
                    self.assertEqual(len(rows_pgt2), 3)
                    self.assertTrue(all(r.source == "fallback" for r in rows_pgt2))
                    # Re-check pgt-001 STILL has 0 rows
                    self.assertEqual(
                        self.session.query(MarketplacePrice).filter_by(product_id="pgt-001").count(),
                        0,
                    )
        finally:
            app.dependency_overrides.pop(get_db, None)
            Path(pid_file).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
