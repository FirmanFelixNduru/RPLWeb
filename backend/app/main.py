"""
CompareBuy — FastAPI Backend Entry Point
"""
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app import scrape_worker
from app.db import is_db_connected, is_fallback_allowed
from app.routers import catalog, scoring, compare, prices
from app.security import RenderSchemeMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown events."""
    prices.price_cache.open()
    print("🚀 CompareBuy API starting up...")
    try:
        yield
    finally:
        print("👋 CompareBuy API shutting down...")
        await prices.price_cache.aclose()
        await asyncio.to_thread(scrape_worker.shutdown_default_supervisor_executor)


app = FastAPI(
    title="CompareBuy API",
    description="Platform Cerdas Perbandingan & Rekomendasi Perangkat Teknologi",
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# CORS — Allow frontend origins
# ──────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RenderSchemeMiddleware)

# ──────────────────────────────────────────────
# Register Routers
# ──────────────────────────────────────────────
app.include_router(catalog.router)
app.include_router(scoring.router)
app.include_router(compare.router)
app.include_router(prices.router)


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "CompareBuy API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health")
def health_check(response: Response):
    """Health readiness check verifying database connectivity."""
    db_ok = is_db_connected()
    if db_ok:
        return {"status": "ok", "database": "connected"}

    if not is_fallback_allowed():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "disconnected"}

    return {"status": "degraded", "database": "disconnected", "fallback": "enabled"}
