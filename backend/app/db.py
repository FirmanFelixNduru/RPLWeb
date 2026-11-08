"""
CompareBuy — Database Connection & Session Management
SQLAlchemy 2.x session factory with graceful fallback handling and W6 timeouts.
"""
import os
import logging
from typing import Generator, Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# W6 Timeout Configuration Constants
PG_CONNECT_TIMEOUT = 5  # seconds
PG_STATEMENT_TIMEOUT_MS = 5000  # ms
PG_IDLE_TRANSACTION_TIMEOUT_MS = 10000  # ms
DB_POOL_TIMEOUT = 10  # seconds
DB_POOL_RECYCLE = 300  # seconds


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
            "options": (
                f"-c statement_timeout={PG_STATEMENT_TIMEOUT_MS} "
                f"-c idle_in_transaction_session_timeout={PG_IDLE_TRANSACTION_TIMEOUT_MS}"
            ),
        }

    return kwargs


load_dotenv()
DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL"))

Base = declarative_base()

engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            **get_engine_kwargs(DATABASE_URL)
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database engine initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize database engine: {e}. Falling back to in-memory mode.")
        engine = None
        SessionLocal = None


def get_db() -> Generator:
    """Dependency that yields a database session if available, else None."""
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_db_connected() -> bool:
    """Check if the database connection is live and reachable."""
    if engine is None or SessionLocal is None:
        return False
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
