import time
from typing import Iterable, List, Optional, Dict
from urllib.parse import urlencode, urljoin, urlparse, parse_qs, urlunparse


import requests
from bs4 import BeautifulSoup

from models import DeviceResult
from parser_ import parse_device_page

TPLC_LIST_URL = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfTPLC/tplc.cfm"

UA = "Mozilla/5.0 (compatible; TPLC-Scraper/1.0)"
TIMEOUT = 20


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def _build_search_url(
    device_name: str,
    product_code: Optional[str],
    min_year: int,
    start_search: int = 1,
    per_page: int = 500,
) -> str:
    """
    Construct the list/search URL. The TPLC UI exposes these params in the URL.
    """
    params = {
        "devicename": device_name,             
        "productcode": product_code or "",    
        "deviceclass": "",
        "regulationnumber": "",
        "min_report_year": min_year,           
        "sortcolumn": "dn",                   
        "start_search": start_search,         
        "pagenum": per_page,                   
    }
    return f"{TPLC_LIST_URL}?{urlencode(params)}"


def _extract_device_links_from_list(html: str, base_url: str) -> List[Dict[str, str]]:
    """
    Return a list of {"url": <abs url>, "name": <device name from list row>}.
    """
    soup = BeautifulSoup(html, "html.parser")
    out: List[Dict[str, str]] = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        if not parsed.path.lower().endswith("tplc.cfm"):
            continue
        qs = {k.lower(): v for k, v in parse_qs(parsed.query).items()}
        if "id" not in qs:
            continue

        if text:
            out.append({"url": abs_url, "name": text})

    seen = set()
    dedup = []
    for item in out:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        dedup.append(item)
    return dedup


def search_and_collect(
    device_name: str,
    product_code: Optional[str],
    min_year: int,
) -> List[Dict[str, str]]:
    sess = _session()
    try:
        sess.get(TPLC_LIST_URL, timeout=TIMEOUT)
    except Exception:
        pass

    device_links: List[Dict[str, str]] = []

    candidates = [
        {"devicename": device_name, "productcode": product_code or "", "regulationnumber": "", "min_report_year": str(min_year), "search": "search"},
        {"device": device_name, "productcode": product_code or "", "regulationnumber": "", "since": str(min_year), "search": "search"},
        {"Device": device_name, "ProductCode": product_code or "", "RegulationNumber": "", "Since": str(min_year), "search": "search"},
    ]

    for payload in candidates:
        try:
            print("POST search with payload:", payload)
            r = sess.post(TPLC_LIST_URL, data=payload, timeout=TIMEOUT)
            r.raise_for_status()
            links = _extract_device_links_from_list(r.text, TPLC_LIST_URL)
            if links:
                device_links = links
                break
        except Exception:
            continue

    if not device_links:
        url = _build_search_url(device_name, product_code, min_year, start_search=1, per_page=500)
        print("Fallback GET Search URL:", url)
        r = sess.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        device_links = _extract_device_links_from_list(r.text, TPLC_LIST_URL)

    print(f"Found {len(device_links)} device links.")
    return device_links

def _ensure_min_year(url: str, min_year: int) -> str:
    """
    Ensure ?min_report_year=YYYY is present (override if already present).
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    qs["min_report_year"] = [str(min_year)]
    new_query = urlencode({k: v[0] if isinstance(v, list) else v for k, v in qs.items()})
    return urlunparse(parsed._replace(query=new_query))


def scrape_device(url: str, min_year: int, fallback_name: Optional[str]) -> DeviceResult:
    sess = _session()
    fixed_url = _ensure_min_year(url, min_year)
    print("Scraping device URL:", fixed_url, " | fallback name:", fallback_name)
    r = sess.get(fixed_url, timeout=TIMEOUT)
    r.raise_for_status()
    return parse_device_page(r.text, fixed_url, fallback_name=fallback_name)

def scrape_devices(links: Iterable[dict], min_year: int) -> List[DeviceResult]:
    out: List[DeviceResult] = []
    for item in links:
        url = item["url"]
        name = item.get("name")
        try:
            out.append(scrape_device(url, min_year, fallback_name=name))
        except Exception:
            continue
        time.sleep(0.5)
    return out

