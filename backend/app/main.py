"""
CompareBuy — FastAPI Backend Entry Point
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import catalog, scoring, compare, prices


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown events."""
    print("🚀 CompareBuy API starting up...")
    yield
    print("👋 CompareBuy API shutting down...")


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
def health_check():
    return {"status": "ok"}
