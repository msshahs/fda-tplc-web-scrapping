from typing import Optional
from fastapi import FastAPI, Query

from models import ScrapeResponse
from scraper import search_and_collect, scrape_devices

app = FastAPI(title="FDA TPLC Device & Patient Problem Extraction API")

@app.get("/scrape", response_model=ScrapeResponse)
def scrape(
    device_name: str = Query(..., description="Device name (substring match)"),
    product_code: Optional[str] = Query(None, description="Optional FDA product code, e.g., DXT"),
    min_year: int = Query(2020, ge=2010, le=2025, description="Minimum report year (default 2020)"),
    limit: int = Query(100, ge=1, le=500, description="Max number of devices to process (default 25)")
):
    try:
        device_links = search_and_collect(device_name, product_code, min_year, max_devices=limit)
        results = scrape_devices(device_links, min_year)
        return ScrapeResponse(
            query={"device_name": device_name, "product_code": product_code, "limit": limit},
            min_year=min_year,
            results=results
        )
    except Exception as e:
        return ScrapeResponse(
            query={"device_name": device_name, "product_code": product_code, "limit": limit, "error": str(e)},
            min_year=min_year,
            results=[]
        )
