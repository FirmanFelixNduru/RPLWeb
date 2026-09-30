"""
CompareBuy — Price Repository
Append-only marketplace price snapshots.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.entities import MarketplacePrice, Marketplace


def save_price_snapshot(
    product_id: str,
    marketplace_code: str,
    price: int,
    seller: str,
    url: str,
    available: bool = True,
    source: str = "fallback",
    captured_at: Optional[str] = None
) -> bool:
    """Save an append-only marketplace price observation snapshot."""
    if SessionLocal is None:
        return False

    db: Session = SessionLocal()
    try:
        mkt = db.query(Marketplace).filter(Marketplace.code == marketplace_code.lower()).first()
        if not mkt:
            mkt = Marketplace(code=marketplace_code.lower(), name=marketplace_code.title())
            db.add(mkt)
            db.flush()

        cap_time = datetime.fromisoformat(captured_at) if captured_at else datetime.now(timezone.utc)

        snapshot = MarketplacePrice(
            product_id=product_id,
            marketplace_id=mkt.id,
            price=price,
            seller=seller,
            url=str(url),
            available=available,
            source=source,
            captured_at=cap_time
        )
        db.add(snapshot)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()
