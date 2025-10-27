from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CountryOut(BaseModel):
    id: int
    name: str
    capital: Optional[str]
    region: Optional[str]
    population: int
    currency_code: Optional[str]
    exchange_rate: Optional[float]
    estimated_gdp: Optional[float]
    flag_url: Optional[str]
    last_refreshed_at: Optional[datetime]

    class Config:
        orm_mode = True


class StatusOut(BaseModel):
    total_countries: int
    last_refreshed_at: Optional[datetime]
