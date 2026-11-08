"""
CompareBuy — SEC-008 Phase 2 (W6): Database Timeout Unit & Integration Tests

Verifies PostgreSQL connection, statement, and idle transaction timeouts,
SQLAlchemy connection pool timeout, session lifecycle, SQLite compatibility,
and fail-closed test environment DB guard.
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend root is in sys.path
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from tests._db_guard import enforce_safe_test_db_env

# Guard environment before any database imports
enforce_safe_test_db_env()

from sqlalchemy import create_engine, text, exc
from app import db
from app.db import (
    PG_CONNECT_TIMEOUT,
    PG_STATEMENT_TIMEOUT_MS,
    PG_IDLE_TRANSACTION_TIMEOUT_MS,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
    get_engine_kwargs,
    normalize_database_url,
    get_db,
)


class TestDatabaseTimeoutsUnit(unittest.TestCase):
    """Unit tests for engine kwargs, timeouts, URL normalization, and SQLite compatibility."""

    def test_w6_constants_values(self):
        """W6 timeout constants match required specifications."""
        self.assertEqual(PG_CONNECT_TIMEOUT, 5)
        self.assertEqual(PG_STATEMENT_TIMEOUT_MS, 5000)
        self.assertEqual(PG_IDLE_TRANSACTION_TIMEOUT_MS, 10000)
        self.assertEqual(DB_POOL_TIMEOUT, 10)
        self.assertEqual(DB_POOL_RECYCLE, 300)

    def test_w6_t01_postgres_connect_timeout(self):
        """W6-T01: PostgreSQL engine kwargs include connect_timeout=5."""
        test_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/comparebuy_test"
        kwargs = get_engine_kwargs(test_url)

        self.assertIn("connect_args", kwargs)
        self.assertIn("connect_timeout", kwargs["connect_args"])
        self.assertEqual(kwargs["connect_args"]["connect_timeout"], 5)

    def test_w6_t02_postgres_statement_timeout_kwarg(self):
        """W6-T02: PostgreSQL engine kwargs set statement_timeout=5000ms."""
        test_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/comparebuy_test"
        kwargs = get_engine_kwargs(test_url)

        self.assertIn("connect_args", kwargs)
        options = kwargs["connect_args"].get("options", "")
        self.assertIn(f"-c statement_timeout={PG_STATEMENT_TIMEOUT_MS}", options)

    def test_w6_t03_postgres_idle_transaction_timeout_kwarg(self):
        """W6-T03: PostgreSQL engine kwargs set idle_in_transaction_session_timeout=10000ms."""
        test_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/comparebuy_test"
        kwargs = get_engine_kwargs(test_url)

        self.assertIn("connect_args", kwargs)
        options = kwargs["connect_args"].get("options", "")
        self.assertIn(
            f"-c idle_in_transaction_session_timeout={PG_IDLE_TRANSACTION_TIMEOUT_MS}",
            options,
        )

    def test_w6_t04_postgres_pool_timeout(self):
        """W6-T04: PostgreSQL engine kwargs include pool_timeout=10."""
        test_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/comparebuy_test"
        kwargs = get_engine_kwargs(test_url)

        self.assertIn("pool_timeout", kwargs)
        self.assertEqual(kwargs["pool_timeout"], 10)

    def test_w6_t05_preserved_pool_settings(self):
        """W6-T05: pool_pre_ping, pool_recycle, and echo=False are preserved across dialects."""
        for url in [
            "postgresql+psycopg2://test_user:test_pass@localhost:5432/comparebuy_test",
            "sqlite:///:memory:",
        ]:
            with self.subTest(url=url):
                kwargs = get_engine_kwargs(url)
                self.assertTrue(kwargs.get("pool_pre_ping"))
                self.assertEqual(kwargs.get("pool_recycle"), 300)
                self.assertFalse(kwargs.get("echo"))

    def test_w6_t06_sqlite_engine_compatibility(self):
        """W6-T06: SQLite engine omits Postgres connect_args & pool_timeout, connects successfully."""
        sqlite_url = "sqlite:///:memory:"
        kwargs = get_engine_kwargs(sqlite_url)

        self.assertNotIn("connect_args", kwargs)
        self.assertNotIn("pool_timeout", kwargs)

        # Ensure creating SQLite engine and executing a query works without error
        eng = create_engine(sqlite_url, **kwargs)
        try:
            with eng.connect() as conn:
                result = conn.execute(text("SELECT 42")).scalar()
                self.assertEqual(result, 42)
        finally:
            eng.dispose()

    def test_w6_t07_session_lifecycle(self):
        """W6-T07: get_db() yields and closes session; yields None when SessionLocal is None."""
        # 1. Normal session lifecycle
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(db, "SessionLocal", mock_factory):
            gen = get_db()
            session = next(gen)
            self.assertIs(session, mock_session)
            mock_session.close.assert_not_called()
            try:
                next(gen)
            except StopIteration:
                pass
            mock_session.close.assert_called_once()

        # 2. Fallback when SessionLocal is None
        with patch.object(db, "SessionLocal", None):
            gen_none = get_db()
            val = next(gen_none)
            self.assertIsNone(val)
            with self.assertRaises(StopIteration):
                next(gen_none)

    def test_w6_t08_db_guard_rejection(self):
        """W6-T08: enforce_safe_test_db_env rejects development DB URL without test in name."""
        unsafe_env = {"DATABASE_URL": "postgresql://postgres:pass@localhost:5432/comparebuy"}
        with self.assertRaises(RuntimeError) as ctx:
            enforce_safe_test_db_env(env=unsafe_env, dotenv_path=None)
        self.assertIn("rejected", str(ctx.exception).lower())

    def test_normalize_database_url(self):
        """normalize_database_url handles postgres://, postgresql://, and sqlite."""
        self.assertEqual(
            normalize_database_url("postgres://user:pass@host:5432/db"),
            "postgresql+psycopg2://user:pass@host:5432/db",
        )
        self.assertEqual(
            normalize_database_url("postgresql://user:pass@host:5432/db"),
            "postgresql+psycopg2://user:pass@host:5432/db",
        )
        self.assertEqual(
            normalize_database_url("postgresql+psycopg2://user:pass@host:5432/db"),
            "postgresql+psycopg2://user:pass@host:5432/db",
        )
        self.assertEqual(
            normalize_database_url("sqlite:///:memory:"),
            "sqlite:///:memory:",
        )
        self.assertIsNone(normalize_database_url(None))


class TestPostgresTimeoutsRuntime(unittest.TestCase):
    """Runtime integration tests against comparebuy_test PostgreSQL instance."""

    @classmethod
    def setUpClass(cls):
        raw_test_url = os.getenv("TEST_DATABASE_URL")
        if not raw_test_url:
            from dotenv import dotenv_values
            dotenv_path = os.path.join(_BACKEND_DIR, ".env")
            raw_test_url = dotenv_values(dotenv_path).get("TEST_DATABASE_URL")

        if not raw_test_url:
            raise unittest.SkipTest("TEST_DATABASE_URL not set; skipping runtime PostgreSQL tests.")

        cls.test_url = normalize_database_url(raw_test_url)
        cls.engine = create_engine(cls.test_url, **get_engine_kwargs(cls.test_url))

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine") and cls.engine is not None:
            cls.engine.dispose()

    def test_runtime_session_timeout_settings(self):
        """Runtime verification of statement_timeout and idle_in_transaction_session_timeout."""
        with self.engine.connect() as conn:
            stmt_timeout = conn.execute(text("SHOW statement_timeout")).scalar()
            idle_timeout = conn.execute(text("SHOW idle_in_transaction_session_timeout")).scalar()

            self.assertIn(stmt_timeout.lower(), ["5s", "5000ms"])
            self.assertIn(idle_timeout.lower(), ["10s", "10000ms"])

    def test_runtime_statement_timeout_cancellation(self):
        """Runtime query exceeding statement_timeout (5s) is cancelled by PostgreSQL."""
        with self.engine.connect() as conn:
            with self.assertRaises(exc.OperationalError) as ctx:
                conn.execute(text("SELECT pg_sleep(6)"))

            # psycopg2.errors.QueryCanceled is wrapped in OperationalError
            orig = getattr(ctx.exception, "orig", None)
            self.assertIsNotNone(orig)
            self.assertIn("canceling statement due to statement timeout", str(orig).lower())


if __name__ == "__main__":
    unittest.main()
