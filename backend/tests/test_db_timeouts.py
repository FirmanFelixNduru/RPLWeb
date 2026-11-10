"""
CompareBuy — SEC-008 Phase 2 (W6): Database Timeout Unit & Integration Tests

Verifies PostgreSQL connection, statement, and idle transaction timeouts,
SQLAlchemy connection pool timeout, session lifecycle, SQLite compatibility,
PoolEvents.connect session initialization handler, and fail-closed test environment DB guard.
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
    init_postgres_session,
    create_db_engine,
    get_db,
)


class FakeCursor:
    """Fake DBAPI cursor recording statements, execution autocommit state, and lifecycle."""

    def __init__(self, connection: FakeDBAPIConnection, fail_on_statement: str | None = None):
        self.connection = connection
        self.fail_on_statement = fail_on_statement
        self.closed = False
        self.executed_statements: list[tuple[str, bool]] = []

    def execute(self, statement: str) -> None:
        if self.closed:
            raise RuntimeError("Cannot execute on closed cursor")
        # Record statement and the connection's autocommit state at execution time
        self.executed_statements.append((statement, self.connection.autocommit))
        self.connection.operation_log.append(("execute", statement, self.connection.autocommit))

        if self.fail_on_statement and self.fail_on_statement in statement:
            raise RuntimeError(f"Simulated execution failure for: {statement}")

    def close(self) -> None:
        self.closed = True
        self.connection.operation_log.append(("cursor_close",))


class FakeDBAPIConnection:
    """Fake DBAPI connection tracking autocommit modifications and cursor operations."""

    def __init__(self, initial_autocommit: bool = False, fail_on_statement: str | None = None):
        self._autocommit = initial_autocommit
        self.fail_on_statement = fail_on_statement
        self.cursor_instance = FakeCursor(self, fail_on_statement=fail_on_statement)
        self.operation_log: list[tuple] = []

    @property
    def autocommit(self) -> bool:
        return self._autocommit

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        self._autocommit = value
        self.operation_log.append(("set_autocommit", value))

    def cursor(self) -> FakeCursor:
        self.operation_log.append(("cursor_open",))
        return self.cursor_instance


class TestPostgresSessionHandlerUnit(unittest.TestCase):
    """Unit tests for init_postgres_session event handler using fake DBAPI connections."""

    def test_handler_enables_autocommit_during_execution(self):
        """Handler activates DBAPI autocommit before executing timeout statements."""
        fake_conn = FakeDBAPIConnection(initial_autocommit=False)
        init_postgres_session(fake_conn)

        self.assertEqual(len(fake_conn.cursor_instance.executed_statements), 2)
        for stmt, autocommit_state in fake_conn.cursor_instance.executed_statements:
            self.assertTrue(autocommit_state, f"Statement {stmt} must be executed with autocommit=True")

        # Verify operation ordering: autocommit set to True occurred before executions
        first_op = fake_conn.operation_log[0]
        self.assertEqual(first_op, ("set_autocommit", True))

    def test_handler_executes_timeout_statements_with_correct_values(self):
        """Handler executes SET statement_timeout and SET idle_in_transaction_session_timeout with W6 values."""
        fake_conn = FakeDBAPIConnection(initial_autocommit=False)
        init_postgres_session(fake_conn)

        expected_stmt = f"SET statement_timeout = {PG_STATEMENT_TIMEOUT_MS}"
        expected_idle = f"SET idle_in_transaction_session_timeout = {PG_IDLE_TRANSACTION_TIMEOUT_MS}"

        executed = [s[0] for s in fake_conn.cursor_instance.executed_statements]
        self.assertEqual(executed, [expected_stmt, expected_idle])

    def test_handler_closes_cursor_after_use(self):
        """Handler explicitly closes the DBAPI cursor after executing statements."""
        fake_conn = FakeDBAPIConnection(initial_autocommit=False)
        init_postgres_session(fake_conn)

        self.assertTrue(fake_conn.cursor_instance.closed)
        self.assertIn(("cursor_close",), fake_conn.operation_log)

    def test_handler_restores_previous_autocommit_when_initially_false(self):
        """Handler restores initial autocommit=False upon successful completion."""
        fake_conn = FakeDBAPIConnection(initial_autocommit=False)
        init_postgres_session(fake_conn)

        self.assertFalse(fake_conn.autocommit)
        self.assertEqual(fake_conn.operation_log[-1], ("set_autocommit", False))

    def test_handler_restores_previous_autocommit_when_initially_true(self):
        """Handler restores initial autocommit=True upon successful completion."""
        fake_conn = FakeDBAPIConnection(initial_autocommit=True)
        init_postgres_session(fake_conn)

        self.assertTrue(fake_conn.autocommit)
        self.assertEqual(fake_conn.operation_log[-1], ("set_autocommit", True))

    def test_handler_restores_autocommit_on_exception_and_propagates(self):
        """Handler closes cursor, restores autocommit, and propagates exception if SQL fails."""
        fake_conn = FakeDBAPIConnection(initial_autocommit=False, fail_on_statement="statement_timeout")

        with self.assertRaises(RuntimeError) as ctx:
            init_postgres_session(fake_conn)

        self.assertIn("Simulated execution failure", str(ctx.exception))
        self.assertTrue(fake_conn.cursor_instance.closed)
        self.assertFalse(fake_conn.autocommit)
        self.assertEqual(fake_conn.operation_log[-1], ("set_autocommit", False))


class TestDatabaseTimeoutsUnit(unittest.TestCase):
    """Unit tests for engine kwargs, timeouts, URL normalization, factory, and SQLite compatibility."""

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

    def test_w6_no_startup_options_reliance(self):
        """W6: Engine kwargs do not rely on PostgreSQL startup options for timeouts."""
        test_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/comparebuy_test"
        kwargs = get_engine_kwargs(test_url)

        # Options should not contain startup options that fail on Supavisor pooler
        options = kwargs.get("connect_args", {}).get("options")
        self.assertIsNone(options, "Startup options must not be used as the timeout mechanism")

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
        """W6-T06: SQLite engine omits Postgres connect_args & pool_timeout, and connects cleanly."""
        sqlite_url = "sqlite:///:memory:"
        kwargs = get_engine_kwargs(sqlite_url)

        self.assertNotIn("connect_args", kwargs)
        self.assertNotIn("pool_timeout", kwargs)

        eng = create_db_engine(sqlite_url)
        try:
            # Verify handler is NOT registered for SQLite
            self.assertNotIn(init_postgres_session, eng.pool.dispatch.connect)

            with eng.connect() as conn:
                result = conn.execute(text("SELECT 42")).scalar()
                self.assertEqual(result, 42)
        finally:
            eng.dispose()

    def test_w6_engine_factory_preserves_config_and_installs_listener(self):
        """create_db_engine installs init_postgres_session listener on PostgreSQL engines."""
        pg_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/comparebuy_test"
        eng = create_db_engine(pg_url)
        try:
            self.assertIn(init_postgres_session, eng.pool.dispatch.connect)
            self.assertEqual(eng.pool.timeout(), 10)
            self.assertEqual(eng.pool._recycle, 300)
            self.assertTrue(eng.pool._pre_ping)
        finally:
            eng.dispose()

    def test_w6_session_lifecycle(self):
        """W6-T07: get_db() yields and closes session; yields None when SessionLocal is None."""
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

        with patch.object(db, "SessionLocal", None):
            gen_none = get_db()
            val = next(gen_none)
            self.assertIsNone(val)
            with self.assertRaises(StopIteration):
                next(gen_none)

    def test_w6_db_guard_rejection(self):
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
        cls.engine = create_db_engine(cls.test_url)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine") and cls.engine is not None:
            cls.engine.dispose()

    def test_runtime_session_timeout_settings(self):
        """Runtime verification of statement_timeout (5s) and idle_in_transaction_session_timeout (10s)."""
        with self.engine.connect() as conn:
            stmt_timeout = conn.execute(text("SHOW statement_timeout")).scalar()
            idle_timeout = conn.execute(text("SHOW idle_in_transaction_session_timeout")).scalar()

            self.assertIn(stmt_timeout.lower(), ["5s", "5000ms"])
            self.assertIn(idle_timeout.lower(), ["10s", "10000ms"])

    def test_runtime_timeout_preserved_after_transaction_and_rollback(self):
        """Runtime verification that timeout settings persist after transaction rollback."""
        with self.engine.connect() as conn:
            trans = conn.begin()
            conn.execute(text("SELECT 1"))
            trans.rollback()

            stmt_timeout = conn.execute(text("SHOW statement_timeout")).scalar()
            idle_timeout = conn.execute(text("SHOW idle_in_transaction_session_timeout")).scalar()

            self.assertIn(stmt_timeout.lower(), ["5s", "5000ms"])
            self.assertIn(idle_timeout.lower(), ["10s", "10000ms"])

    def test_runtime_new_physical_connection_configuration(self):
        """Runtime verification that freshly opened physical connections receive timeout configuration."""
        self.engine.dispose()

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

            orig = getattr(ctx.exception, "orig", None)
            self.assertIsNotNone(orig)
            self.assertIn("canceling statement due to statement timeout", str(orig).lower())


if __name__ == "__main__":
    unittest.main()
