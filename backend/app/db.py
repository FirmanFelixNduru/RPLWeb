"""
CompareBuy — Database Connection & Session Management
SQLAlchemy 2.x session factory with explicit fail-closed policy, W6 timeouts, and secure logging.
"""
import os
import re
import logging
from enum import Enum
from typing import Generator, Optional
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url, Engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# W6 Timeout Configuration Constants
PG_CONNECT_TIMEOUT = 5  # seconds
PG_STATEMENT_TIMEOUT_MS = 5000  # ms
PG_IDLE_TRANSACTION_TIMEOUT_MS = 10000  # ms
DB_POOL_TIMEOUT = 10  # seconds
DB_POOL_RECYCLE = 300  # seconds


class DatabaseStatus(str, Enum):
    CONNECTED = "connected"
    UNCONFIGURED = "unconfigured"
    INIT_FAILED = "init_failed"
    DISCONNECTED = "disconnected"


def scrub_db_secrets(text: str) -> str:
    """Scrub database URLs, passwords, and credentials from log and error strings."""
    if not text:
        return ""
    scrubbed = re.sub(
        r'(postgres(?:ql)?(?:\+[a-zA-Z0-9_-]+)?:\/\/)([^:@\s]+):([^@\s]+)@',
        r'\1\2:***@',
        str(text)
    )
    scrubbed = re.sub(r'password=[^\s;]+', 'password=***', scrubbed, flags=re.IGNORECASE)
    return scrubbed


def get_app_env() -> str:
    """Return canonical application environment: 'production', 'development', or 'test'.
    
    Defaults to 'production' if not explicitly set, ensuring fail-closed safety.
    If RENDER=true, environment is strictly 'production'.
    """
    if os.getenv("RENDER", "").strip().lower() == "true":
        return "production"
    raw = os.getenv("APP_ENV", "").strip().lower()
    if raw in ("development", "dev"):
        return "development"
    if raw in ("test", "testing"):
        return "test"
    if raw == "production":
        return "production"
    raw_env = os.getenv("ENVIRONMENT", "").strip().lower()
    if raw_env in ("development", "dev"):
        return "development"
    if raw_env in ("test", "testing"):
        return "test"
    return "production"


def is_production_mode() -> bool:
    """Return True if running in production mode."""
    return get_app_env() == "production"


def is_fallback_allowed() -> bool:
    """Return True if in-memory catalogue fallback is explicitly permitted.
    
    STRICT POLICY:
    - In production mode (or on Render), fallback is ALWAYS FORBIDDEN (returns False).
    - In development or test mode, fallback is allowed ONLY IF explicitly enabled
      via ALLOW_CATALOG_FALLBACK=true.
    """
    if is_production_mode():
        return False
    raw_fallback = os.getenv("ALLOW_CATALOG_FALLBACK", "").strip().lower()
    return raw_fallback in ("true", "1", "yes")


def normalize_database_url(url: Optional[str]) -> Optional[str]:
    """Normalize postgres:// to postgresql+psycopg2:// for SQLAlchemy compatibility."""
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def get_engine_kwargs(url_str: str) -> dict:
    """Return driver-appropriate engine arguments ensuring W6 timeouts and SQLite compatibility."""
    url = make_url(url_str)
    backend = url.get_backend_name()

    kwargs: dict = {
        "pool_pre_ping": True,
        "pool_recycle": DB_POOL_RECYCLE,
        "echo": False,
    }

    if backend in ("postgresql", "postgres"):
        kwargs["pool_timeout"] = DB_POOL_TIMEOUT
        kwargs["connect_args"] = {
            "connect_timeout": PG_CONNECT_TIMEOUT,
        }

    return kwargs


def init_postgres_session(dbapi_connection, connection_record=None) -> None:
    """Apply W6 PostgreSQL session timeouts via PoolEvents.connect under autocommit."""
    prev_autocommit = getattr(dbapi_connection, "autocommit", False)
    try:
        dbapi_connection.autocommit = True
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"SET statement_timeout = {PG_STATEMENT_TIMEOUT_MS}")
            cursor.execute(f"SET idle_in_transaction_session_timeout = {PG_IDLE_TRANSACTION_TIMEOUT_MS}")
        finally:
            cursor.close()
    finally:
        dbapi_connection.autocommit = prev_autocommit


def create_db_engine(url_str: str, **extra_kwargs) -> Engine:
    """Factory creating SQLAlchemy engine with driver kwargs and PostgreSQL session timeout listener."""
    url = make_url(url_str)
    backend = url.get_backend_name()
    kwargs = get_engine_kwargs(url_str)
    if extra_kwargs:
        kwargs.update(extra_kwargs)

    eng = create_engine(url_str, **kwargs)

    if backend in ("postgresql", "postgres"):
        event.listen(eng, "connect", init_postgres_session)

    return eng


load_dotenv()
DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL"))

Base = declarative_base()

engine = None
SessionLocal = None
_engine_init_error: Optional[str] = None

if DATABASE_URL:
    try:
        engine = create_db_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database engine initialized successfully.")
    except Exception as e:
        _engine_init_error = type(e).__name__
        logger.warning(
            "Could not initialize database engine (%s). Fallback allowed: %s",
            _engine_init_error,
            is_fallback_allowed(),
        )
        engine = None
        SessionLocal = None


def get_database_status() -> DatabaseStatus:
    """Return current detailed database connectivity status."""
    if not DATABASE_URL:
        return DatabaseStatus.UNCONFIGURED
    if engine is None or SessionLocal is None:
        return DatabaseStatus.INIT_FAILED
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return DatabaseStatus.CONNECTED
    except Exception:
        return DatabaseStatus.DISCONNECTED


def get_db() -> Generator:
    """Dependency that yields a database session if available.
    
    Fail-closed in production: if SessionLocal is not available, fails-closed
    immediately with HTTP 503 Service Unavailable.
    In development/test: if fallback is explicitly permitted, yields None.
    """
    if SessionLocal is None:
        if not is_fallback_allowed():
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable"
            )
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_db_connected() -> bool:
    """Check if the database connection is live and reachable."""
    return get_database_status() == DatabaseStatus.CONNECTED
