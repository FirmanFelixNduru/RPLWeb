"""Disposable worker-process isolation and deadline supervisor for SEC-008 AC-08.

Architecture (Decisions D6, D7, D8, D9 + RC-01/RC-03 Hardening):
- One disposable child process per shared flight executes marketplace HTTP fetching
  and HTML parsing only, launched via `subprocess.Popen` with a strict OS environment
  allowlist (`WORKER_ENV_ALLOWLIST` + `WORKER_FIXED_ENV`) and neutral temp `cwd` so
  DB credentials/secrets in parent `os.environ` are never inherited at OS spawn and
  parent `os.environ` is never mutated.
- Residual OS boundary (F-05 / RC-03): child still runs under the same OS user (`UID`)
  as the parent; preventing explicit-path reads of host files like `backend/.env`
  requires external OS account/ACL or container user/mount isolation.
- Parent process owns the monotonic 35-second lifecycle deadline (starting BEFORE
  process creation and ending ONLY after worker exit confirmation, reaping, and IPC
  handle closure), strict JSON payload validation, fallback assembly, DB persistence,
  and TTL cache publication.
"""
from __future__ import annotations

import asyncio
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
import functools
import json
import logging
import multiprocessing
import multiprocessing.connection
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import threading
from time import monotonic
from typing import Callable, Optional

from app.models import MarketplacePrice

logger = logging.getLogger(__name__)

_MP_CTX = multiprocessing.get_context("spawn")
_ORIG_MP_PROCESS = _MP_CTX.Process
_ORIG_MP_PIPE = _MP_CTX.Pipe
_BACKEND_ROOT = str(Path(__file__).resolve().parents[1])

PRICE_SCRAPE_MAX_CONCURRENT_ENV = "PRICE_SCRAPE_MAX_CONCURRENT"
# shortcut: provisional safeguard (NOT container-optimal; target container RAM/vCPU/replicas unspecified in repo).
# Measured Windows 11 final-launcher profile: ~54.4 MiB peak RSS/worker (~217.8 MiB for 4 workers + ~88 MiB parent RSS),
# 3 outbound HTTP requests/worker (12 concurrent at 4 workers), 1 Uvicorn worker; tune via PRICE_SCRAPE_MAX_CONCURRENT.
DEFAULT_MAX_CONCURRENT_SCRAPES = 4

WORKER_ENV_ALLOWLIST = frozenset(
    {
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "SYSTEMDRIVE",
        "PATH",
        "PATHEXT",
        "TEMP",
        "TMP",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "TZ",
    }
)
WORKER_FIXED_ENV: dict[str, str] = {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONNOUSERSITE": "1",
}

MAX_IPC_PAYLOAD_BYTES = 16_384
DEFAULT_CLEANUP_RESERVE_SECONDS = 2.0
MAX_TERMINATE_GRACE_SECONDS = 0.4
POLL_SLICE_SECONDS = 0.01

ALLOWED_MARKETPLACES = frozenset({"Tokopedia", "Shopee", "Lazada"})
MIN_VALID_PRICE = 50_000
MAX_VALID_PRICE = 150_000_000

_DEFAULT_EXEC_LOCK = threading.Lock()
_DEFAULT_SUPERVISOR_EXECUTOR: Optional[ThreadPoolExecutor] = None
_ACTIVE_WORKERS_LOCK = threading.Lock()
_ACTIVE_WORKER_PIDS: set[int] = set()


def active_worker_pids() -> list[int]:
    """Return sorted OS PIDs of sanitized subprocess workers not yet confirmed stopped & reaped."""
    with _ACTIVE_WORKERS_LOCK:
        return sorted(_ACTIVE_WORKER_PIDS)


def build_worker_env(source_env: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    """Build minimal allowlisted child environment without mutating parent `os.environ`."""
    src = os.environ if source_env is None else source_env
    sanitized = {
        key: val
        for key in WORKER_ENV_ALLOWLIST
        if isinstance((val := src.get(key)), str) and val != ""
    }
    sanitized.update(WORKER_FIXED_ENV)
    return sanitized


def parse_max_concurrent_scrapes(raw: Optional[str] = None) -> int:
    """Parse and validate `PRICE_SCRAPE_MAX_CONCURRENT` as a positive integer (>= 1)."""
    source = os.getenv(PRICE_SCRAPE_MAX_CONCURRENT_ENV) if raw is None else raw
    if source is None:
        return DEFAULT_MAX_CONCURRENT_SCRAPES
    if not isinstance(source, str):
        raise ValueError("PRICE_SCRAPE_MAX_CONCURRENT must be a string or None")
    cleaned = source.strip()
    if cleaned == "":
        return DEFAULT_MAX_CONCURRENT_SCRAPES
    try:
        value = int(cleaned, 10)
    except ValueError:
        raise ValueError(
            f"PRICE_SCRAPE_MAX_CONCURRENT must be a positive integer, got {source!r}"
        ) from None
    if value < 1:
        raise ValueError(f"PRICE_SCRAPE_MAX_CONCURRENT must be >= 1, got {value}")
    return value


def _get_default_supervisor_executor() -> ThreadPoolExecutor:
    global _DEFAULT_SUPERVISOR_EXECUTOR
    with _DEFAULT_EXEC_LOCK:
        if _DEFAULT_SUPERVISOR_EXECUTOR is None:
            _DEFAULT_SUPERVISOR_EXECUTOR = ThreadPoolExecutor(
                max_workers=parse_max_concurrent_scrapes(),
                thread_name_prefix="scrape-supervisor",
            )
        return _DEFAULT_SUPERVISOR_EXECUTOR


def shutdown_default_supervisor_executor(*, wait: bool = True) -> None:
    global _DEFAULT_SUPERVISOR_EXECUTOR
    with _DEFAULT_EXEC_LOCK:
        executor = _DEFAULT_SUPERVISOR_EXECUTOR
        _DEFAULT_SUPERVISOR_EXECUTOR = None
    if executor is not None:
        executor.shutdown(wait=wait, cancel_futures=True)


class ScrapeOverloadError(RuntimeError):
    """Raised when bounded scrape worker admission capacity is full or closing."""


class ScrapeTimeoutError(TimeoutError):
    """Raised when the total scraping worker lifecycle budget is exceeded."""

    def __init__(
        self,
        message: str = "Marketplace price lookup timed out",
        *,
        budget: float = 0.0,
        elapsed: float = 0.0,
        worker_pid: Optional[int] = None,
        exitcode: Optional[int] = None,
        worker_stopped: bool = False,
        reaped: bool = False,
        within_budget: bool = False,
    ) -> None:
        super().__init__(message)
        self.budget = budget
        self.elapsed = elapsed
        self.worker_pid = worker_pid
        self.exitcode = exitcode
        self.worker_stopped = worker_stopped
        self.reaped = reaped
        self.within_budget = within_budget


class ScrapeWorkerError(RuntimeError):
    """Raised when the scrape worker crashes, exits non-zero, or emits invalid IPC data."""


class ScrapeWorkerCleanupError(ScrapeWorkerError):
    """Raised if the OS fails to confirm worker termination within the lifecycle deadline."""

    def __init__(
        self,
        message: str = "Failed to confirm scrape worker termination",
        *,
        worker_pid: Optional[int] = None,
        unreaped_proc: object = None,
    ) -> None:
        super().__init__(message)
        self.worker_pid = worker_pid
        self.unreaped_proc = unreaped_proc


class _WorkerCancelledSignal(Exception):
    """Internal synchronous signal translated to `asyncio.CancelledError` on the event loop."""


@dataclass(frozen=True)
class WorkerFlightOutcome:
    offers: list[MarketplacePrice]
    worker_pid: Optional[int]
    exitcode: Optional[int]
    started_at: float
    finished_at: float
    deadline: float
    cleanup_reserve: float
    reaped: bool


def compute_cleanup_reserve(budget_seconds: float) -> float:
    """Reserve deterministic termination + kill + reap margin inside total budget.

    Empirical Windows 11 measurements (`Python 3.13`, `spawn`):
    - Realistic worker `spawn` + `httpx`/`bs4` import + parse + IPC + reap: ~0.89s–0.94s.
    - `terminate()` / `kill()` + `join()` + handle `close()` on CPU-spinning child: ~0.006s–0.007s.
    Reserving 2.0s on the 35.0s budget (25% capped at 2.0s, floor 0.05s) provides >250x
    the measured Windows kill+reap time while preserving 33.0s for spawn + concurrent HTTP/parse.
    """
    if budget_seconds <= 0:
        return 0.0
    return min(DEFAULT_CLEANUP_RESERVE_SECONDS, max(0.05, budget_seconds * 0.25))


# ──────────────────────────────────────────────────────────────────────
# Child Process Target & Pure Marketplace Fetching/Parsing
# ──────────────────────────────────────────────────────────────────────
async def _scrape_one_marketplace(
    product_name: str,
    marketplace: str,
    search_url: str,
    price_selector: str,
    title_selector: str,
    seller_label: str,
    *,
    headers: dict[str, str],
    timeout,
    parse_listing_fn: Callable,
    transport_factory: Optional[Callable] = None,
) -> Optional[dict]:
    import httpx

    try:
        client_kwargs = {
            "headers": headers,
            "timeout": timeout,
            "follow_redirects": True,
        }
        if transport_factory is not None:
            client_kwargs["transport"] = transport_factory()
        async with httpx.AsyncClient(**client_kwargs) as client:
            resp = await client.get(search_url)
            if resp.status_code == 200:
                price = await asyncio.to_thread(
                    parse_listing_fn,
                    resp.text,
                    price_selector,
                    title_selector,
                    product_name,
                )
                if price:
                    return {
                        "marketplace": marketplace,
                        "price": int(price),
                        "url": search_url,
                        "seller": seller_label,
                        "available": True,
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                    }
    except Exception as exc:
        logger.warning("%s worker scraping failed: %s", marketplace, exc)
    return None


async def _scrape_all_marketplaces_async(
    product_name: str,
    *,
    transport_factory: Optional[Callable] = None,
) -> list[dict]:
    from app.scraper import HEADERS, TIMEOUT, _parse_listing

    encoded_q = product_name.replace(" ", "+")
    specs = (
        (
            "Tokopedia",
            f"https://www.tokopedia.com/search?q={encoded_q}",
            '[data-testid="spnSRPProdPrice"]',
            '[data-testid="spnSRPProdName"]',
            "Tokopedia Seller",
        ),
        (
            "Shopee",
            f"https://shopee.co.id/search?keyword={encoded_q}",
            ".shopee-price",
            ".shopee-search-item-result__item-name",
            "Shopee Seller",
        ),
        (
            "Lazada",
            f"https://www.lazada.co.id/catalog/?q={encoded_q}",
            ".price--NVB62",
            ".title--wFj93",
            "Lazada Seller",
        ),
    )
    results = await asyncio.gather(
        *(
            _scrape_one_marketplace(
                product_name,
                mp,
                url,
                price_sel,
                title_sel,
                seller,
                headers=HEADERS,
                timeout=TIMEOUT,
                parse_listing_fn=_parse_listing,
                transport_factory=transport_factory,
            )
            for mp, url, price_sel, title_sel, seller in specs
        ),
        return_exceptions=True,
    )
    offers: list[dict] = []
    for item in results:
        if isinstance(item, dict):
            offers.append(item)
    return offers


def scrape_marketplaces_worker(
    product_id: str,
    product_name: str,
    *,
    transport_factory: Optional[Callable] = None,
) -> list[dict]:
    """Default `spawn`-safe worker function executing HTTP fetch + HTML parse without DB access."""
    return asyncio.run(
        _scrape_all_marketplaces_async(product_name, transport_factory=transport_factory)
    )


_SCRUBBED_ENV_SUBSTRINGS = ("SECRET", "PASSWORD", "TOKEN", "PRIVATE_KEY", "API_KEY")


def _scrub_worker_environ() -> None:
    """Scrub DB and credential-named env vars inside the child process (never mutates parent)."""
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("TEST_DATABASE_URL", None)
    for key in list(os.environ.keys()):
        upper_key = key.upper()
        if any(marker in upper_key for marker in _SCRUBBED_ENV_SUBSTRINGS):
            os.environ.pop(key, None)


def _worker_entry(
    send_conn,
    worker_fn: Callable[[str, str], list[dict]],
    product_id: str,
    product_name: str,
) -> None:
    """Top-level child entry point (`spawn`-safe).

    Note (F-05): Post-spawn scrubbing reduces accidental in-process exposure before
    `worker_fn` executes without mutating parent `os.environ`, but is NOT a security
    sandbox against hostile code execution (child inherits parent env at OS spawn and
    runs under the same OS user/working directory).
    """
    _scrub_worker_environ()
    exit_code = 0
    try:
        offers = worker_fn(product_id, product_name)
        envelope = {"status": "ok", "offers": offers}
        raw = json.dumps(envelope, allow_nan=False).encode("utf-8")
        if len(raw) > MAX_IPC_PAYLOAD_BYTES:
            raise ValueError(f"Worker IPC payload size {len(raw)} exceeds {MAX_IPC_PAYLOAD_BYTES} bytes")
        send_conn.send_bytes(raw)
    except BaseException as exc:
        exit_code = 1
        try:
            err_raw = json.dumps(
                {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "message": str(exc)[:300],
                }
            ).encode("utf-8")
            if len(err_raw) <= MAX_IPC_PAYLOAD_BYTES:
                send_conn.send_bytes(err_raw)
        except Exception:
            pass
    finally:
        try:
            send_conn.close()
        except Exception:
            pass
    if exit_code != 0:
        sys.exit(exit_code)


# ──────────────────────────────────────────────────────────────────────
# Parent-Side Strict IPC Payload Validation & Worker Supervision
# ──────────────────────────────────────────────────────────────────────
def validate_worker_payload(raw_bytes: bytes) -> list[MarketplacePrice]:
    """Validate untrusted JSON bytes from the disposable worker into `MarketplacePrice` models."""
    from app.scraper import is_valid_marketplace_url

    if not isinstance(raw_bytes, (bytes, bytearray)) or len(raw_bytes) == 0:
        raise ScrapeWorkerError("Empty IPC payload from scrape worker")
    if len(raw_bytes) > MAX_IPC_PAYLOAD_BYTES:
        raise ScrapeWorkerError("Oversize IPC payload from scrape worker")

    try:
        decoded = json.loads(bytes(raw_bytes).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScrapeWorkerError(f"Malformed worker JSON payload: {type(exc).__name__}") from None

    if not isinstance(decoded, dict) or decoded.get("status") != "ok":
        err_type = decoded.get("error_type", "unknown") if isinstance(decoded, dict) else "invalid"
        raise ScrapeWorkerError(f"Worker reported error payload ({err_type})")

    raw_offers = decoded.get("offers")
    if not isinstance(raw_offers, list) or len(raw_offers) > len(ALLOWED_MARKETPLACES):
        raise ScrapeWorkerError("Worker offers field must be a list of at most 3 marketplaces")

    validated: list[MarketplacePrice] = []
    seen_marketplaces: set[str] = set()
    allowed_keys = {"marketplace", "price", "url", "seller", "available", "captured_at"}

    for entry in raw_offers:
        if not isinstance(entry, dict) or set(entry.keys()) != allowed_keys:
            raise ScrapeWorkerError("Worker offer entry has invalid schema keys")

        marketplace = entry["marketplace"]
        price = entry["price"]
        url = entry["url"]
        seller = entry["seller"]
        available = entry["available"]
        captured_at = entry["captured_at"]

        if not isinstance(marketplace, str) or marketplace not in ALLOWED_MARKETPLACES:
            raise ScrapeWorkerError(f"Invalid worker marketplace: {marketplace!r}")
        if marketplace in seen_marketplaces:
            raise ScrapeWorkerError(f"Duplicate marketplace in worker payload: {marketplace}")
        seen_marketplaces.add(marketplace)

        if isinstance(price, bool) or not isinstance(price, int):
            raise ScrapeWorkerError("Worker offer price must be an integer")
        if price < MIN_VALID_PRICE or price > MAX_VALID_PRICE:
            raise ScrapeWorkerError(f"Worker offer price out of sanity bounds: {price}")

        if not isinstance(url, str) or not is_valid_marketplace_url(url):
            raise ScrapeWorkerError("Worker offer URL failed official marketplace domain check")

        if not isinstance(seller, str) or not (1 <= len(seller.strip()) <= 200):
            raise ScrapeWorkerError("Worker offer seller is invalid")

        if not isinstance(available, bool):
            raise ScrapeWorkerError("Worker offer available flag must be bool")

        if not isinstance(captured_at, str) or not captured_at.strip():
            raise ScrapeWorkerError("Worker offer captured_at must be a non-empty ISO timestamp")
        try:
            datetime.fromisoformat(captured_at)
        except ValueError:
            raise ScrapeWorkerError("Worker offer captured_at is not valid ISO-8601") from None

        validated.append(
            MarketplacePrice(
                marketplace=marketplace,
                price=price,
                url=url,
                seller=seller,
                available=available,
                source="scraped",
                captured_at=captured_at,
            )
        )

    return validated


def _safe_close_conn(conn) -> None:
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def try_reap_process_nonblocking(proc) -> tuple[bool, bool]:
    """Check without blocking whether `proc` has exited and close its OS handle if stopped."""
    if proc is None:
        return True, True
    try:
        if proc.is_alive():
            proc.join(timeout=0.0)
        stopped = (not proc.is_alive()) and (proc.exitcode is not None)
    except ValueError:
        return True, True
    except Exception:
        return False, False
    if not stopped:
        return False, False
    try:
        proc.close()
        return True, True
    except ValueError:
        return True, True
    except Exception:
        return True, False


def _terminate_and_reap(proc, recv_conn, deadline: float) -> tuple[bool, bool, Optional[int]]:
    """Stop accepting worker output, terminate/escalate-kill child, confirm exit, and reap handles."""
    _safe_close_conn(recv_conn)
    if proc is None:
        return True, True, None

    if proc.is_alive():
        try:
            proc.terminate()
        except Exception:
            pass
        remaining = max(0.0, deadline - monotonic())
        term_grace = min(MAX_TERMINATE_GRACE_SECONDS, remaining * 0.25)
        try:
            proc.join(timeout=term_grace)
        except Exception:
            pass

    if proc.is_alive():
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.join(timeout=max(0.0, deadline - monotonic()))
        except Exception:
            pass

    if proc.is_alive():
        try:
            proc.join(timeout=0.0)
        except Exception:
            pass

    stopped = (not proc.is_alive()) and (proc.exitcode is not None)
    exitcode = proc.exitcode
    reaped = False
    if stopped:
        try:
            proc.close()
            reaped = True
        except Exception:
            reaped = False

    return stopped, reaped, exitcode


def _try_recv_once(recv_conn) -> tuple[Optional[bytes], Optional[str]]:
    """Non-blocking poll + bounded frame read handling Windows BrokenPipeError / POSIX EOFError."""
    try:
        if recv_conn.poll(0):
            data = recv_conn.recv_bytes(MAX_IPC_PAYLOAD_BYTES + 1)
            return data, None
        return None, None
    except (EOFError, BrokenPipeError, OSError) as exc:
        return None, f"IPC closed without complete frame ({type(exc).__name__})"
    except BufferError:
        return None, f"Worker IPC frame exceeded {MAX_IPC_PAYLOAD_BYTES} bytes"


_SUBPROCESS_BOOTSTRAP = """
import importlib, importlib.util, json, os, struct, sys

os.environ.pop("__PYVENV_LAUNCHER__", None)
sys._cb_initial_spawn_env = dict(os.environ)
ipc_fd = os.dup(1)
if os.name == "nt":
    import msvcrt
    msvcrt.setmode(ipc_fd, os.O_BINARY)
devnull_fd = os.open(os.devnull, os.O_WRONLY)
os.dup2(devnull_fd, 1)
os.close(devnull_fd)

cfg = json.loads(sys.argv[1])
for p in reversed(cfg["sys_path"]):
    if p and p not in sys.path:
        sys.path.insert(0, p)

loaded_files = {}
def _load_callable(spec):
    mod_name, qual_name, mod_file = spec["module"], spec["qualname"], spec.get("file")
    if mod_name == "__main__" and mod_file:
        mod = loaded_files.get(mod_file)
        if mod is None:
            mspec = importlib.util.spec_from_file_location("_cb_worker_main", mod_file)
            mod = importlib.util.module_from_spec(mspec)
            sys.modules["_cb_worker_main"] = mod
            mspec.loader.exec_module(mod)
            loaded_files[mod_file] = mod
    else:
        mod = importlib.import_module(mod_name)
    obj = mod
    for attr in qual_name.split("."):
        obj = getattr(obj, attr)
    return obj

class _FdSendConn:
    def __init__(self, fd):
        self._fd = fd
    def send_bytes(self, data):
        if self._fd < 0:
            raise OSError("IPC pipe is closed")
        payload = memoryview(data)
        frame = struct.pack(">I", len(payload)) + payload.tobytes()
        view = memoryview(frame)
        sent = 0
        while sent < len(view):
            sent += os.write(self._fd, view[sent:])
    def close(self):
        if self._fd >= 0:
            fd, self._fd = self._fd, -1
            os.close(fd)

conn = _FdSendConn(ipc_fd)
try:
    entry_fn = _load_callable(cfg["entry"])
    worker_fn = _load_callable(cfg["worker"])
    entry_fn(conn, worker_fn, cfg["product_id"], cfg["product_name"])
finally:
    conn.close()
"""


def _callable_spec(fn: Callable) -> tuple[dict[str, Optional[str]], Optional[str]]:
    mod_name = getattr(fn, "__module__", None)
    qual_name = getattr(fn, "__qualname__", None)
    if not mod_name or not qual_name or "<locals>" in qual_name:
        raise ValueError(f"Worker callable {fn!r} must be an importable top-level function")
    mod = sys.modules.get(mod_name)
    mod_file = str(Path(mod.__file__).resolve()) if getattr(mod, "__file__", None) else None
    extra_dir = str(Path(mod_file).parent) if (mod_name == "__main__" and mod_file) else None
    return {"module": mod_name, "qualname": qual_name, "file": mod_file}, extra_dir


class _SubprocessRecvConn:
    """Framed single-message stdout pipe reader matching `PipeConnection` semantics."""

    def __init__(self, stream) -> None:
        self._stream = stream
        self._fd = stream.fileno()
        self._wake = threading.Event()
        self._lock = threading.Lock()
        self._frame: Optional[bytes] = None
        self._oversize = False
        self._eof = False
        self._consumed = False
        self._closed = False
        self._reader = threading.Thread(target=self._read_loop, name="scrape-ipc-read", daemon=True)
        self._reader.start()

    @staticmethod
    def _read_exact_fd(fd: int, n: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < n:
            piece = os.read(fd, n - len(chunks))
            if not piece:
                break
            chunks.extend(piece)
        return bytes(chunks)

    def _read_loop(self) -> None:
        try:
            hdr = self._read_exact_fd(self._fd, 4)
            if len(hdr) < 4:
                with self._lock:
                    self._eof = True
                return
            (size,) = struct.unpack(">I", hdr)
            if size > MAX_IPC_PAYLOAD_BYTES:
                with self._lock:
                    self._oversize = True
                return
            body = self._read_exact_fd(self._fd, size)
            with self._lock:
                if len(body) < size:
                    self._eof = True
                else:
                    self._frame = body
        except Exception:
            with self._lock:
                self._eof = True
        finally:
            self._wake.set()

    def wait_activity(self, timeout: float) -> None:
        self._wake.wait(timeout=timeout)

    def poll(self, timeout: float = 0.0) -> bool:
        if timeout > 0:
            self._wake.wait(timeout=timeout)
        with self._lock:
            if self._closed:
                return False
            return (not self._consumed) and (self._frame is not None or self._oversize or self._eof)

    def recv_bytes(self, maxlength: Optional[int] = None) -> bytes:
        with self._lock:
            if self._closed or self._consumed:
                raise EOFError("IPC frame unavailable")
            self._consumed = True
            if self._oversize:
                raise BufferError("Oversize IPC frame")
            if self._frame is None:
                raise EOFError("IPC closed before complete frame")
            if maxlength is not None and len(self._frame) > maxlength:
                raise BufferError("Oversize IPC frame")
            return self._frame

    def close(self) -> None:
        # Never call BufferedReader.close() while child may still hold pipe write-end open
        # (BufferedReader C mutex would block before proc.terminate/kill can run); _SubprocessWorker.close()
        # closes popen.stdout once the child process has exited and OS released the pipe write-end.
        with self._lock:
            self._closed = True
        self._wake.set()

    def finalize_stream(self) -> None:
        self._reader.join(timeout=0.2)
        try:
            self._stream.close()
        except Exception:
            pass


class _SubprocessWorker:
    """Process lifecycle adapter around `subprocess.Popen` matching `multiprocessing.Process`."""

    def __init__(self, popen: subprocess.Popen, recv_conn: _SubprocessRecvConn) -> None:
        self._popen = popen
        self._recv_conn = recv_conn
        self.pid: Optional[int] = popen.pid
        self._closed = False
        if self.pid is not None:
            with _ACTIVE_WORKERS_LOCK:
                _ACTIVE_WORKER_PIDS.add(self.pid)

    @property
    def exitcode(self) -> Optional[int]:
        return self._popen.poll()

    def is_alive(self) -> bool:
        return self._popen.poll() is None

    def terminate(self) -> None:
        self._popen.terminate()

    def kill(self) -> None:
        self._popen.kill()

    def join(self, timeout: Optional[float] = None) -> None:
        try:
            self._popen.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            pass

    def close(self) -> None:
        if self._popen.poll() is None:
            raise ValueError("Cannot close a running worker process")
        if not self._closed:
            self._closed = True
            self._recv_conn.finalize_stream()
            if self.pid is not None:
                with _ACTIVE_WORKERS_LOCK:
                    _ACTIVE_WORKER_PIDS.discard(self.pid)


def _launch_sanitized_worker(
    entry_target: Callable,
    worker_fn: Callable[[str, str], list[dict]],
    product_id: str,
    product_name: str,
) -> tuple[_SubprocessRecvConn, _SubprocessWorker]:
    entry_spec, entry_dir = _callable_spec(entry_target)
    worker_spec, worker_dir = _callable_spec(worker_fn)
    sys_path = [_BACKEND_ROOT]
    for extra in (entry_dir, worker_dir):
        if extra and extra not in sys_path:
            sys_path.append(extra)
    payload = json.dumps(
        {
            "sys_path": sys_path,
            "entry": entry_spec,
            "worker": worker_spec,
            "product_id": product_id,
            "product_name": product_name,
        }
    )
    python_exe = sys.executable
    child_env = build_worker_env()
    base_exe = getattr(sys, "_base_executable", None)
    if os.name == "nt" and base_exe and os.path.normcase(base_exe) != os.path.normcase(python_exe):
        child_env["__PYVENV_LAUNCHER__"] = python_exe
        python_exe = base_exe
    popen = subprocess.Popen(
        [python_exe, "-c", _SUBPROCESS_BOOTSTRAP, payload],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=child_env,
        cwd=tempfile.gettempdir(),
        close_fds=True,
    )
    recv_conn = _SubprocessRecvConn(popen.stdout)
    return recv_conn, _SubprocessWorker(popen, recv_conn)


def _supervise_worker_sync(
    product_id: str,
    product_name: str,
    *,
    started_at: float,
    budget_seconds: float,
    deadline: float,
    cleanup_reserve: float,
    cancel_event: threading.Event,
    worker_fn: Callable[[str, str], list[dict]],
    pre_spawn_hook: Optional[Callable[[], None]],
    on_stopping: Optional[Callable[[], None]],
    entry_target: Callable,
    deadline_cap_fn: Optional[Callable[[], Optional[float]]] = None,
) -> WorkerFlightOutcome:
    def _effective_deadline() -> float:
        cap = deadline_cap_fn() if deadline_cap_fn is not None else None
        return deadline if cap is None else min(deadline, cap)

    work_cutoff = deadline - cleanup_reserve

    if cancel_event.is_set():
        if on_stopping is not None:
            on_stopping()
        raise _WorkerCancelledSignal()

    if pre_spawn_hook is not None:
        pre_spawn_hook()

    if cancel_event.is_set():
        if on_stopping is not None:
            on_stopping()
        raise _WorkerCancelledSignal()

    if monotonic() >= work_cutoff:
        if on_stopping is not None:
            on_stopping()
        finish = monotonic()
        raise ScrapeTimeoutError(
            "Marketplace price lookup timed out before worker spawn",
            budget=budget_seconds,
            elapsed=finish - started_at,
            worker_pid=None,
            exitcode=None,
            worker_stopped=True,
            reaped=True,
            within_budget=(finish <= deadline),
        )

    recv_conn = None
    send_conn = None
    proc = None
    worker_pid: Optional[int] = None

    try:
        use_mocked_mp = (_MP_CTX.Process != _ORIG_MP_PROCESS) or (_MP_CTX.Pipe != _ORIG_MP_PIPE)
        if use_mocked_mp:
            recv_conn, send_conn = _MP_CTX.Pipe(duplex=False)
            proc = _MP_CTX.Process(
                target=entry_target,
                args=(send_conn, worker_fn, product_id, product_name),
                daemon=True,
            )
            proc.start()
            worker_pid = proc.pid
            _safe_close_conn(send_conn)
            send_conn = None
        else:
            recv_conn, proc = _launch_sanitized_worker(entry_target, worker_fn, product_id, product_name)
            worker_pid = proc.pid

        raw_payload: Optional[bytes] = None
        ipc_error: Optional[str] = None

        while monotonic() < work_cutoff and not cancel_event.is_set():
            if raw_payload is None and ipc_error is None:
                raw_payload, ipc_error = _try_recv_once(recv_conn)

            if not proc.is_alive():
                break

            slice_timeout = min(max(0.0, work_cutoff - monotonic()), POLL_SLICE_SECONDS)
            if slice_timeout > 0:
                if use_mocked_mp:
                    wait_handles = (
                        [proc.sentinel]
                        if (raw_payload is not None or ipc_error is not None)
                        else [recv_conn, proc.sentinel]
                    )
                    try:
                        multiprocessing.connection.wait(wait_handles, timeout=slice_timeout)
                    except (OSError, ValueError):
                        break
                elif raw_payload is not None or ipc_error is not None:
                    proc.join(timeout=slice_timeout)
                else:
                    recv_conn.wait_activity(slice_timeout)

        # 1. Cancellation check (all waiters stopped waiting or service shutting down)
        if cancel_event.is_set():
            if on_stopping is not None:
                on_stopping()
            stopped, reaped, _ = _terminate_and_reap(proc, recv_conn, _effective_deadline())
            unreaped = proc
            proc = None
            recv_conn = None
            if not (stopped and reaped):
                raise ScrapeWorkerCleanupError(
                    "Failed to confirm worker stop/reap after cancellation",
                    worker_pid=worker_pid,
                    unreaped_proc=unreaped,
                )
            raise _WorkerCancelledSignal()

        # 2. Cutoff / deadline check if worker has NOT exited yet -> discard any partial/early frame!
        if proc.is_alive() or monotonic() >= _effective_deadline():
            if on_stopping is not None:
                on_stopping()
            stopped, reaped, ec = _terminate_and_reap(proc, recv_conn, _effective_deadline())
            unreaped = proc
            proc = None
            recv_conn = None
            finish = monotonic()
            if not (stopped and reaped):
                raise ScrapeWorkerCleanupError(
                    f"Worker PID {worker_pid} could not be confirmed stopped/reaped within budget",
                    worker_pid=worker_pid,
                    unreaped_proc=unreaped,
                )
            raise ScrapeTimeoutError(
                "Marketplace price lookup timed out",
                budget=budget_seconds,
                elapsed=finish - started_at,
                worker_pid=worker_pid,
                exitcode=ec,
                worker_stopped=stopped,
                reaped=reaped,
                within_budget=(finish <= deadline),
            )

        # 3. Worker exited before work_cutoff: drain final frame if buffered, join & reap within deadline
        if raw_payload is None and ipc_error is None:
            raw_payload, ipc_error = _try_recv_once(recv_conn)

        proc.join(timeout=max(0.0, deadline - monotonic()))
        if proc.is_alive():
            if on_stopping is not None:
                on_stopping()
            stopped, reaped, ec = _terminate_and_reap(proc, recv_conn, deadline)
            unreaped = proc
            proc = None
            recv_conn = None
            finish = monotonic()
            if not (stopped and reaped):
                raise ScrapeWorkerCleanupError(
                    f"Worker PID {worker_pid} failed to join within budget",
                    worker_pid=worker_pid,
                    unreaped_proc=unreaped,
                )
            raise ScrapeTimeoutError(
                "Marketplace price lookup timed out during worker join",
                budget=budget_seconds,
                elapsed=finish - started_at,
                worker_pid=worker_pid,
                exitcode=ec,
                worker_stopped=stopped,
                reaped=reaped,
                within_budget=(finish <= deadline),
            )

        exitcode = proc.exitcode
        _safe_close_conn(recv_conn)
        recv_conn = None
        proc.close()
        proc = None
        finished_at = monotonic()

        if finished_at > deadline:
            if on_stopping is not None:
                on_stopping()
            raise ScrapeTimeoutError(
                "Marketplace price lookup timed out during worker reap",
                budget=budget_seconds,
                elapsed=finished_at - started_at,
                worker_pid=worker_pid,
                exitcode=exitcode,
                worker_stopped=True,
                reaped=True,
                within_budget=False,
            )

        if exitcode != 0:
            if on_stopping is not None:
                on_stopping()
            raise ScrapeWorkerError(f"Scrape worker exited with non-zero code {exitcode}")

        if ipc_error is not None or raw_payload is None:
            if on_stopping is not None:
                on_stopping()
            raise ScrapeWorkerError(ipc_error or "Scrape worker exited 0 without sending IPC payload")

        offers = validate_worker_payload(raw_payload)
        return WorkerFlightOutcome(
            offers=offers,
            worker_pid=worker_pid,
            exitcode=exitcode,
            started_at=started_at,
            finished_at=finished_at,
            deadline=deadline,
            cleanup_reserve=cleanup_reserve,
            reaped=True,
        )
    except BaseException as active_exc:
        if proc is not None:
            stopped, reaped, _ = _terminate_and_reap(proc, recv_conn, max(deadline, monotonic() + 0.2))
            unreaped = proc
            proc = None
            recv_conn = None
            if not (stopped and reaped) and not isinstance(active_exc, ScrapeWorkerCleanupError):
                raise ScrapeWorkerCleanupError(
                    f"Worker PID {worker_pid} cleanup failed after {type(active_exc).__name__}",
                    worker_pid=worker_pid,
                    unreaped_proc=unreaped,
                ) from active_exc
        raise
    finally:
        _safe_close_conn(send_conn)
        _safe_close_conn(recv_conn)
        if proc is not None:
            _terminate_and_reap(proc, None, max(deadline, monotonic() + 0.2))


async def run_isolated_scrape_flight(
    product_id: str,
    product_name: str,
    *,
    budget_seconds: float,
    cancel_event: Optional[threading.Event] = None,
    worker_fn: Callable[[str, str], list[dict]] = scrape_marketplaces_worker,
    pre_spawn_hook: Optional[Callable[[], None]] = None,
    on_stopping: Optional[Callable[[], None]] = None,
    executor: Optional[ThreadPoolExecutor] = None,
    deadline_cap_fn: Optional[Callable[[], Optional[float]]] = None,
    _entry_override: Optional[Callable] = None,
) -> WorkerFlightOutcome:
    """Spawn one disposable worker process and supervise its complete 35s lifecycle."""
    # D6 / AC08-01: Monotonic deadline starts strictly BEFORE process creation.
    started_at = monotonic()
    budget = float(budget_seconds)
    deadline = started_at + budget
    cleanup_reserve = compute_cleanup_reserve(budget)
    effective_cancel = cancel_event if cancel_event is not None else threading.Event()
    entry_target = _entry_override if _entry_override is not None else _worker_entry
    target_executor = executor if executor is not None else _get_default_supervisor_executor()

    loop = asyncio.get_running_loop()
    sup_future = loop.run_in_executor(
        target_executor,
        functools.partial(
            _supervise_worker_sync,
            product_id,
            product_name,
            started_at=started_at,
            budget_seconds=budget,
            deadline=deadline,
            cleanup_reserve=cleanup_reserve,
            cancel_event=effective_cancel,
            worker_fn=worker_fn,
            pre_spawn_hook=pre_spawn_hook,
            on_stopping=on_stopping,
            entry_target=entry_target,
            deadline_cap_fn=deadline_cap_fn,
        ),
    )
    try:
        return await asyncio.shield(sup_future)
    except _WorkerCancelledSignal:
        raise asyncio.CancelledError from None
    except asyncio.CancelledError:
        effective_cancel.set()
        from app.scraper import _drain_task

        await _drain_task(sup_future)
        if not sup_future.cancelled():
            sup_exc = sup_future.exception()
            if isinstance(sup_exc, ScrapeWorkerCleanupError):
                raise sup_exc
        raise
