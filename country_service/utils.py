import requests
from typing import List, Dict, Any, Optional
import random
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont

COUNTRIES_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"


def fetch_countries(timeout: int = 10) -> List[Dict[str, Any]]:
    resp = requests.get(COUNTRIES_API, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_exchange_rates(timeout: int = 10) -> Dict[str, Any]:
    resp = requests.get(EXCHANGE_API, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # The exchange API has structure: {"result":"success", "rates": {"NGN":1600, ...}}
    return data


def pick_currency_code(country_item: Dict[str, Any]) -> Optional[str]:
    currencies = country_item.get("currencies") or []
    if not currencies:
        return None
    first = currencies[0]
    return first.get("code")


def compute_estimated_gdp(population: int, exchange_rate: Optional[float]) -> Optional[float]:
    if population is None:
        return None
    if exchange_rate is None:
        # specification: if currency missing -> set 0 or null depending on case
        return None
    multiplier = random.uniform(1000.0, 2000.0)
    # avoid division by zero
    if exchange_rate == 0:
        return None
    return (population * multiplier) / float(exchange_rate)


def compute_estimated_gdp_for_missing_currency(population: int) -> float:
    # When currencies array is empty: estimated_gdp = 0
    return 0.0


def generate_summary_image(total: int, top5: List[Dict[str, Any]], timestamp: datetime, out_path: str):
    # Simple generated image with white background
    width = 800
    height = 600
    bg = (255, 255, 255)
    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", size=20)
        title_font = ImageFont.truetype("arial.ttf", size=26)
    except Exception:
        font = ImageFont.load_default()
        title_font = font

    y = 20
    draw.text((20, y), f"Countries cached: {total}", fill=(0, 0, 0), font=title_font)
    y += 40
    draw.text((20, y), f"Last refresh: {timestamp.isoformat()}", fill=(0, 0, 0), font=font)
    y += 40
    draw.text((20, y), "Top 5 Countries by estimated_gdp:", fill=(0, 0, 0), font=title_font)
    y += 30

    for idx, c in enumerate(top5, start=1):
        name = c.get("name")
        gdp = c.get("estimated_gdp")
        gdp_str = "N/A" if gdp is None else f"{gdp:,.2f}"
        draw.text((30, y), f"{idx}. {name} — {gdp_str}", fill=(0, 0, 0), font=font)
        y += 28

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
