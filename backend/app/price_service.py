"""Process-local TTL cache and identity-guarded single-flight for the price endpoint."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import threading
from time import monotonic
from typing import Callable, Optional

from app import scrape_worker, scraper
from app.models import PriceResponse

logger = logging.getLogger(__name__)

PRICE_CACHE_TTL_SECONDS = 300
# shortcut: 5s drain fits inside Docker's 10s default SIGTERM grace; raise container stop-grace if scaled up.
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class ShutdownDrainResult:
    clean: bool
    drained_flights: int
    quarantined_keys: tuple[tuple[str, str], ...]


def _retrieve_unobserved_task_exception(task: asyncio.Task) -> None:
    """Mark flight task exception retrieved if all shielded waiters cancelled before completion."""
    if not task.cancelled():
        task.exception()


@dataclass
class _Flight:
    key: tuple[str, str]
    cancel_event: threading.Event = field(default_factory=threading.Event)
    stopped_event: asyncio.Event = field(default_factory=asyncio.Event)
    task: Optional[asyncio.Task] = None
    waiters: int = 0
    state: str = "RUNNING"  # RUNNING -> STOPPING -> QUARANTINED | STOPPED
    holds_permit: bool = False
    unreaped_proc: object = None
    shutdown_deadline: Optional[float] = None


class PriceCache:
    # shortcut: one backend event loop owns this cache; coordinate externally for multiple workers.
    def __init__(
        self,
        *,
        worker_fn: Callable[[str, str], list[dict]] = scrape_worker.scrape_marketplaces_worker,
        max_concurrent: Optional[int] = None,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
    ):
        if max_concurrent is None:
            resolved_max = scrape_worker.parse_max_concurrent_scrapes()
        else:
            if isinstance(max_concurrent, bool) or not isinstance(max_concurrent, int):
                raise TypeError("max_concurrent must be an integer")
            if max_concurrent < 1:
                raise ValueError("max_concurrent must be >= 1")
            resolved_max = max_concurrent
        self._max_concurrent: int = resolved_max
        self._shutdown_timeout: float = max(0.0, float(shutdown_timeout))
        self._lifecycle_state: str = "OPEN"  # OPEN -> CLOSING -> CLOSED
        self._active_permits: int = 0
        self._executor: Optional[ThreadPoolExecutor] = None
        self._cache: dict[tuple[str, str], tuple[float, PriceResponse]] = {}
        self._inflight: dict[tuple[str, str], _Flight] = {}
        self._worker_fn = worker_fn

    def open(self) -> None:
        """Re-enable cache admissions on application lifespan startup."""
        self._reap_recovered_quarantined()
        self._lifecycle_state = "OPEN"

    def _ensure_executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_concurrent,
                thread_name_prefix="scrape-supervisor",
            )
        return self._executor

    def _try_recover_quarantined(self, flight: _Flight) -> bool:
        """Reap a quarantined worker if the OS now confirms exit; return True iff recovered."""
        if flight.state != "QUARANTINED":
            return False
        if flight.unreaped_proc is not None:
            stopped, reaped = scrape_worker.try_reap_process_nonblocking(flight.unreaped_proc)
            if not (stopped and reaped):
                return False
        flight.unreaped_proc = None
        flight.state = "STOPPED"
        if self._inflight.get(flight.key) is flight:
            del self._inflight[flight.key]
        self._release_permit(flight)
        return True

    def _reap_recovered_quarantined(self) -> None:
        for candidate in list(self._inflight.values()):
            if candidate.state == "QUARANTINED":
                self._try_recover_quarantined(candidate)

    def _acquire_permit(self, flight: _Flight) -> None:
        self._reap_recovered_quarantined()
        if self._active_permits >= self._max_concurrent:
            raise scrape_worker.ScrapeOverloadError("Marketplace price lookup busy")
        self._active_permits += 1
        flight.holds_permit = True

    def _release_permit(self, flight: _Flight) -> None:
        if flight.holds_permit:
            flight.holds_permit = False
            self._active_permits = max(0, self._active_permits - 1)

    def _evict_expired(self, now: float) -> None:
        for expired in [k for k, (deadline, _) in self._cache.items() if deadline <= now]:
            del self._cache[expired]

    async def get(self, product_id: str, product_name: str) -> PriceResponse:
        key = (product_id, product_name)

        while True:
            if self._lifecycle_state != "OPEN":
                raise scrape_worker.ScrapeOverloadError("Marketplace price lookup busy")

            now = monotonic()
            self._evict_expired(now)
            if key in self._cache:
                return self._cache[key][1].model_copy(deep=True)

            existing = self._inflight.get(key)
            if existing is not None and existing.state != "RUNNING":
                if existing.state == "QUARANTINED":
                    if self._try_recover_quarantined(existing):
                        continue
                    raise scrape_worker.ScrapeWorkerCleanupError(
                        f"Previous scrape worker for {product_id!r} has not confirmed termination",
                        worker_pid=getattr(existing.unreaped_proc, "pid", None),
                        unreaped_proc=existing.unreaped_proc,
                    )
                # Wait boundedly for stopping flight to confirm worker exit/reap (no duplicate spawn).
                wait_bound = max(0.01, float(scraper.TOTAL_SCRAPE_TIMEOUT_SECONDS))
                wait_started = monotonic()
                try:
                    await asyncio.wait_for(existing.stopped_event.wait(), timeout=wait_bound)
                except TimeoutError:
                    raise scrape_worker.ScrapeTimeoutError(
                        "Marketplace price lookup timed out waiting for stopping worker",
                        budget=wait_bound,
                        elapsed=monotonic() - wait_started,
                        worker_pid=getattr(existing.unreaped_proc, "pid", None),
                        worker_stopped=False,
                        reaped=False,
                        within_budget=False,
                    ) from None
                continue

            # No await between lookup, admission check, and insertion: atomic on the application's event loop.
            if existing is None:
                flight = _Flight(key=key)
                self._acquire_permit(flight)
                flight.task = asyncio.create_task(self._fetch(flight))
                flight.task.add_done_callback(_retrieve_unobserved_task_exception)
                self._inflight[key] = flight
            else:
                flight = existing
            break

        flight.waiters += 1
        try:
            result = await asyncio.shield(flight.task)
            return result.model_copy(deep=True)
        finally:
            flight.waiters -= 1
            if flight.waiters == 0 and flight.task is not None and not flight.task.done():
                flight.state = "STOPPING"
                flight.cancel_event.set()
                flight.task.cancel()
                await scraper._drain_task(flight.task)

    async def _fetch(self, flight: _Flight) -> PriceResponse:
        product_id, product_name = flight.key
        now_wib = datetime.now(scraper.WIB).strftime("%Y-%m-%d %H:%M:%S WIB")
        utc_now_iso = datetime.now(timezone.utc).isoformat()

        def mark_stopping() -> None:
            if flight.state == "RUNNING":
                flight.state = "STOPPING"

        try:
            outcome = await scrape_worker.run_isolated_scrape_flight(
                product_id,
                product_name,
                budget_seconds=float(scraper.TOTAL_SCRAPE_TIMEOUT_SECONDS),
                cancel_event=flight.cancel_event,
                worker_fn=self._worker_fn,
                on_stopping=mark_stopping,
                executor=self._ensure_executor(),
                deadline_cap_fn=lambda: flight.shutdown_deadline,
            )

            if (
                flight.cancel_event.is_set()
                or flight.state != "RUNNING"
                or self._inflight.get(flight.key) is not flight
            ):
                raise asyncio.CancelledError

            result = scraper.build_price_response(
                product_id,
                product_name,
                outcome.offers,
                now_label=now_wib,
            )

            # Parent-only persistence (outside the 35s worker budget per D6).
            await scraper._run_blocking(scraper._save_snapshots, product_id, result.prices, utc_now_iso)

            if (
                flight.cancel_event.is_set()
                or flight.state != "RUNNING"
                or self._inflight.get(flight.key) is not flight
            ):
                raise asyncio.CancelledError

            self._cache[flight.key] = (
                monotonic() + PRICE_CACHE_TTL_SECONDS,
                result.model_copy(deep=True),
            )
            return result
        except scrape_worker.ScrapeWorkerCleanupError as cleanup_err:
            unreaped = getattr(cleanup_err, "unreaped_proc", None)
            if unreaped is not None:
                stopped, reaped = scrape_worker.try_reap_process_nonblocking(unreaped)
                if not (stopped and reaped):
                    flight.unreaped_proc = unreaped
                    flight.state = "QUARANTINED"
            if flight.state == "RUNNING":
                flight.state = "STOPPING"
            raise
        except BaseException:
            if flight.state == "RUNNING":
                flight.state = "STOPPING"
            raise
        finally:
            if flight.state != "QUARANTINED":
                flight.state = "STOPPED"
                if self._inflight.get(flight.key) is flight:
                    del self._inflight[flight.key]
                self._release_permit(flight)
            flight.stopped_event.set()

    async def aclose(self, timeout: Optional[float] = None) -> ShutdownDrainResult:
        """Stop accepting requests, terminate/reap active workers, and close the supervisor executor."""
        self._lifecycle_state = "CLOSING"
        self._cache.clear()

        drain_budget = self._shutdown_timeout if timeout is None else max(0.0, float(timeout))
        shutdown_deadline = monotonic() + drain_budget

        flights = list(self._inflight.values())
        pending_tasks: list[asyncio.Task] = []
        for flight in flights:
            flight.shutdown_deadline = shutdown_deadline
            if flight.state == "RUNNING":
                flight.state = "STOPPING"
            flight.cancel_event.set()
            if flight.task is not None and not flight.task.done():
                flight.task.cancel()
                pending_tasks.append(flight.task)

        if pending_tasks:
            wait_cap = max(0.05, (shutdown_deadline - monotonic()) + 0.5)
            try:
                await asyncio.wait_for(
                    asyncio.gather(*(scraper._drain_task(t) for t in pending_tasks), return_exceptions=True),
                    timeout=wait_cap,
                )
            except TimeoutError:
                pass

        for q_flight in list(self._inflight.values()):
            if q_flight.state != "QUARANTINED":
                continue
            if self._try_recover_quarantined(q_flight):
                continue
            if q_flight.unreaped_proc is not None and monotonic() < shutdown_deadline:
                stopped, reaped, _ = await asyncio.to_thread(
                    scrape_worker._terminate_and_reap,
                    q_flight.unreaped_proc,
                    None,
                    shutdown_deadline,
                )
                if stopped and reaped:
                    q_flight.unreaped_proc = None
                    q_flight.state = "STOPPED"
                    if self._inflight.get(q_flight.key) is q_flight:
                        del self._inflight[q_flight.key]
                    self._release_permit(q_flight)

        any_unfinished_task = any(
            f.task is not None and not f.task.done() for f in self._inflight.values()
        )
        if self._executor is not None and not any_unfinished_task:
            executor = self._executor
            self._executor = None
            await asyncio.to_thread(executor.shutdown, True, cancel_futures=True)

        self._lifecycle_state = "CLOSED"
        quarantined_keys = tuple(sorted(k for k, f in self._inflight.items() if f.state != "STOPPED"))
        if quarantined_keys:
            logger.error("PriceCache shutdown left unconfirmed flights: %s", quarantined_keys)
        return ShutdownDrainResult(
            clean=(len(quarantined_keys) == 0),
            drained_flights=len(flights),
            quarantined_keys=quarantined_keys,
        )


price_cache = PriceCache()
