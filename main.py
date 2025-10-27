from fastapi import FastAPI, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from country_service import crud, database, models, schemas
from country_service.database import SessionLocal, init_db
from dotenv import load_dotenv
import os
from typing import List, Optional
from datetime import datetime
import requests

load_dotenv()

app = FastAPI(title="Country Currency & Exchange API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    # import models Base
    init_db(models.Base)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # Return consistent 400 JSON
    details = {}
    for err in exc.errors():
        loc = ".".join([str(x) for x in err.get("loc", [])])
        msg = err.get("msg")
        details[loc] = msg
    return JSONResponse(status_code=400, content={"error": "Validation failed", "details": details})


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Country not found"})


@app.get("/countries", response_model=List[schemas.CountryOut])
def list_countries(region: Optional[str] = Query(None), currency: Optional[str] = Query(None), sort: Optional[str] = Query(None), db: Session = Depends(get_db)):
    countries = crud.get_countries(db, region=region, currency=currency, sort=sort)
    return countries

@app.get("/countries/image")
def get_image():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "cache", "summary.png")
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Summary image not found"})
    return FileResponse(path, media_type="image/png")

@app.get("/countries/{name}", response_model=schemas.CountryOut)
def get_country(name: str = Path(...), db: Session = Depends(get_db)):
    c = crud.get_country_by_name(db, name)
    if not c:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return c


@app.delete("/countries/{name}")
def delete_country(name: str = Path(...), db: Session = Depends(get_db)):
    success = crud.delete_country_by_name(db, name)
    if not success:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    db.commit()
    return JSONResponse(status_code=200, content={"deleted": name})


@app.post("/countries/refresh")
def refresh_countries(db: Session = Depends(get_db)):
    # Perform refresh; if external API fails, return 503 and do not touch DB
    try:
        # crud.refresh_countries will fetch external APIs first
        result = crud.refresh_countries(db)
        db.commit()
        return JSONResponse(status_code=200, content={
            "inserted": result.get("inserted"),
            "updated": result.get("updated"),
            "total": result.get("total"),
            "last_refreshed_at": result.get("last_refreshed_at").isoformat() if result.get("last_refreshed_at") else None,
        })
    except requests.exceptions.RequestException:
        db.rollback()
        return JSONResponse(status_code=503, content={"error": "External data source unavailable", "details": "Could not fetch data from external API"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": "Internal server error"})


@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    meta = db.query(models.RefreshMeta).first()
    total = meta.total_countries if meta else db.query(models.Country).count()
    last = meta.last_refreshed_at if meta else None
    return JSONResponse(status_code=200, content={"total_countries": total, "last_refreshed_at": last.isoformat() if last else None})



