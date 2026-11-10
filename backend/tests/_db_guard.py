"""Pre-import database and network safety helpers for backend tests (SEC-008 T-17).

Prevents accidental connections or writes to the development database (`comparebuy`)
when running `unittest discover` or standalone test scripts, while never printing
database credentials or secrets. Uses pure stdlib `urllib.parse` so importing `tests`
never pulls `sqlalchemy` or `app.db` into spawned worker processes.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping, Optional
from urllib.parse import urlsplit

from dotenv import dotenv_values

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_DOTENV_PATH = _BACKEND_DIR / ".env"


def empty_scrape_worker(product_id: str, product_name: str) -> list[dict]:
    """Top-level spawn-safe deterministic worker returning zero live offers (triggers parent fallback)."""
    return []


def offline_price_endpoint_context(suppress_persistence: bool = True):
    """Context manager isolating `/api/prices/{id}` from live marketplace network in tests."""
    from contextlib import ExitStack
    import inspect
    import sys
    from unittest.mock import AsyncMock, patch
    from app import price_service, scraper
    from app.routers import prices

    stack = ExitStack()
    if suppress_persistence:
        stack.enter_context(patch("app.repositories.price_repo.save_price_snapshot", return_value=False))

    from app.db import get_db
    from app.main import app

    def _offline_get_db():
        yield None

    stack.enter_context(patch.dict(app.dependency_overrides, {get_db: _offline_get_db}))

    main_file = getattr(sys.modules.get("__main__"), "__file__", "") or ""
    if main_file.replace("\\", "/").endswith("/tests/test_api.py"):
        # `tests/test_api.py` executes at module top-level without `if __name__ == "__main__":`,
        # so spawning on Windows when `test_api.py` is `__main__` would re-execute `test_api.py` in `__mp_main__`.
        from app import scrape_worker

        outcome = scrape_worker.WorkerFlightOutcome(
            offers=[],
            worker_pid=None,
            exitcode=0,
            started_at=0.0,
            finished_at=0.0,
            deadline=35.0,
            cleanup_reserve=2.0,
            reaped=True,
        )
        stack.enter_context(patch.object(prices, "price_cache", price_service.PriceCache()))
        stack.enter_context(
            patch.object(scrape_worker, "run_isolated_scrape_flight", AsyncMock(return_value=outcome))
        )
    elif "worker_fn" in inspect.signature(price_service.PriceCache.__init__).parameters:
        stack.enter_context(
            patch.object(prices, "price_cache", price_service.PriceCache(worker_fn=empty_scrape_worker))
        )
    else:
        stack.enter_context(patch.object(prices, "price_cache", price_service.PriceCache()))
        for attr in ("_scrape_tokopedia", "_scrape_shopee", "_scrape_lazada"):
            stack.enter_context(patch.object(scraper, attr, AsyncMock(return_value=None)))
    return stack


def _extract_db_identity(raw_url: str) -> tuple[str, int, str]:
    """Extract `(host, port, database)` using stdlib `urlsplit` without exposing credentials."""
    parts = urlsplit(raw_url.strip())
    if not parts.scheme or "://" not in raw_url:
        raise ValueError("Missing URL scheme")
    try:
        port = parts.port or 5432
    except ValueError as exc:
        raise ValueError("Invalid URL port") from exc
    host = (parts.hostname or "localhost").lower()
    db_name = (parts.path or "").lstrip("/").strip()
    return host, port, db_name


def _parse_and_validate_test_url(raw_url: str, var_name: str, dev_identity: Optional[tuple]) -> None:
    """Validate that a database URL points strictly to an isolated `*test*` DB.

    Never includes passwords or raw URLs in exception messages.
    """
    try:
        host, port, db_name = _extract_db_identity(raw_url)
    except Exception:
        raise RuntimeError(f"{var_name} is not a valid database URL.") from None

    if "test" not in db_name.lower():
        raise RuntimeError(
            f"Unsafe {var_name} rejected before app import: database '{db_name or '<empty>'}' "
            "does not contain 'test'."
        )

    if dev_identity is not None and (host, port, db_name) == dev_identity:
        raise RuntimeError(
            f"Unsafe {var_name} rejected before app import: target matches configured "
            "development database."
        )


def enforce_safe_test_db_env(
    env: Optional[MutableMapping[str, str]] = None,
    dotenv_path: Optional[Path] = _DEFAULT_DOTENV_PATH,
) -> None:
    """Fail-closed guard executed BEFORE importing `app.db` or `app.main`."""
    target_env = os.environ if env is None else env

    dev_identity: Optional[tuple] = None
    if dotenv_path is not None and Path(dotenv_path).is_file():
        raw_dotenv_db = (dotenv_values(dotenv_path).get("DATABASE_URL") or "").strip()
        if raw_dotenv_db:
            try:
                host, port, db_name = _extract_db_identity(raw_dotenv_db)
                if "test" not in db_name.lower():
                    dev_identity = (host, port, db_name)
            except Exception:
                pass

    raw_db_url = target_env.get("DATABASE_URL")
    if raw_db_url is None:
        target_env["DATABASE_URL"] = ""
    elif raw_db_url.strip():
        _parse_and_validate_test_url(raw_db_url.strip(), "DATABASE_URL", dev_identity)

    raw_test_url = target_env.get("TEST_DATABASE_URL")
    if raw_test_url and raw_test_url.strip():
        _parse_and_validate_test_url(raw_test_url.strip(), "TEST_DATABASE_URL", dev_identity)

    # In test runs where safe test DB is enforced without an explicit TEST_DATABASE_URL:
    target_env.setdefault("APP_ENV", "test")
    target_env.setdefault("ALLOW_CATALOG_FALLBACK", "true")
