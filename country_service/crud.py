from sqlalchemy.orm import Session
from . import models, utils
from datetime import datetime
from sqlalchemy import func
from typing import Optional, List, Dict, Any
import traceback

CACHE_IMAGE_PATH = "cache/summary.png"


def refresh_countries(db: Session) -> Dict[str, Any]:
    # Fetch external data first; if either fails, raise an exception (caller will return 503)
    countries_data = utils.fetch_countries()
    exchange_data = utils.fetch_exchange_rates()

    rates = {}
    if isinstance(exchange_data, dict):
        rates = exchange_data.get("rates", {})

    now = datetime.utcnow()

    # We'll perform upserts within DB session; do not commit until complete
    updated = 0
    inserted = 0

    for item in countries_data:
        try:
            name = item.get("name")
            capital = item.get("capital")
            region = item.get("region")
            population = item.get("population") or 0
            flag = item.get("flag")

            currency_code = utils.pick_currency_code(item)

            if currency_code is None:
                exchange_rate = None
                estimated_gdp = 0.0
            else:
                exchange_rate = rates.get(currency_code)
                if exchange_rate is None:
                    estimated_gdp = None
                else:
                    estimated_gdp = utils.compute_estimated_gdp(population, exchange_rate)

            # Look for existing country by name (case-insensitive)
            existing = db.query(models.Country).filter(func.lower(models.Country.name) == func.lower(name)).first()
            if existing:
                existing.capital = capital
                existing.region = region
                existing.population = population
                existing.currency_code = currency_code
                existing.exchange_rate = exchange_rate
                # special handling when currencies array empty -> estimated_gdp = 0
                if currency_code is None:
                    existing.estimated_gdp = 0.0
                else:
                    existing.estimated_gdp = estimated_gdp
                existing.flag_url = flag
                existing.last_refreshed_at = now
                updated += 1
            else:
                c = models.Country(
                    name=name,
                    capital=capital,
                    region=region,
                    population=population,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=(0.0 if currency_code is None else estimated_gdp),
                    flag_url=flag,
                    last_refreshed_at=now,
                )
                db.add(c)
                inserted += 1
        except Exception:
            # Skip problematic items but continue; do not abort entire refresh
            traceback.print_exc()
            continue

    # Update refresh meta
    total = db.query(models.Country).count()
    meta = db.query(models.RefreshMeta).first()
    if not meta:
        meta = models.RefreshMeta(total_countries=total, last_refreshed_at=now)
        db.add(meta)
    else:
        meta.total_countries = total
        meta.last_refreshed_at = now

    db.flush()

    # Generate image: top 5 by estimated_gdp (desc), treating None as -inf
    top5_q = db.query(models.Country).order_by(models.Country.estimated_gdp.desc()).limit(5).all()
    top5 = [
        {
            "name": c.name,
            "estimated_gdp": c.estimated_gdp,
        }
        for c in top5_q
    ]
    # Save image on disk
    utils.generate_summary_image(total, top5, now, CACHE_IMAGE_PATH)

    return {"inserted": inserted, "updated": updated, "total": total, "last_refreshed_at": now}


def get_countries(db: Session, region: Optional[str] = None, currency: Optional[str] = None, sort: Optional[str] = None) -> List[models.Country]:
    q = db.query(models.Country)
    if region:
        q = q.filter(models.Country.region == region)
    if currency:
        q = q.filter(models.Country.currency_code == currency)
    if sort == "gdp_desc":
        q = q.order_by(models.Country.estimated_gdp.desc())
    elif sort == "gdp_asc":
        q = q.order_by(models.Country.estimated_gdp.asc())
    return q.all()


def get_country_by_name(db: Session, name: str) -> Optional[models.Country]:
    return db.query(models.Country).filter(func.lower(models.Country.name) == func.lower(name)).first()


def delete_country_by_name(db: Session, name: str) -> bool:
    c = get_country_by_name(db, name)
    if not c:
        return False
    db.delete(c)
    return True
