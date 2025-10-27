from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression
from sqlalchemy import null

Base = declarative_base()


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    capital = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True)
    population = Column(Integer, nullable=False)
    currency_code = Column(String(16), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String(1024), nullable=True)
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)


class RefreshMeta(Base):
    __tablename__ = "refresh_meta"

    id = Column(Integer, primary_key=True, default=1)
    total_countries = Column(Integer, nullable=False, default=0)
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)
