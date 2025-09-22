import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from typing import Optional

from models import DeviceResult, ProblemItem

def _int_or_none(text: str | None):
    if not text:
        return None
    digits = re.findall(r"\d+", text.replace(",", ""))
    return int("".join(digits)) if digits else None

def _abs(base_url: str, href: str | None) -> str | None:
    return urljoin(base_url, href) if href else None

def _row_count_from_anchor(a_tag) -> int | None:
    tr = a_tag.find_parent("tr")
    if not tr:
        return None
    cells = tr.find_all(["td", "th"])
    for td in cells[1:3]:
        val = _int_or_none(td.get_text(strip=True))
        if val is not None:
            return val
    return _int_or_none(tr.get_text(" ", strip=True))

def _extract_device_name_from_table(soup: BeautifulSoup) -> Optional[str]:
    """
    Prefer rows like:  [Device Name]  [Injector And Syringe, Angiographic]
    """
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        for idx, c in enumerate(cells):
            label = c.get_text(" ", strip=True).lower()
            if "device name" in label or label == "device":

                if idx + 1 < len(cells):
                    name = cells[idx + 1].get_text(" ", strip=True)
                    if name and len(name) > 2:
                        return name
    return None

def _extract_device_name_generic(soup: BeautifulSoup) -> Optional[str]:
    for tag in soup.find_all(["b", "strong"]):
        txt = tag.get_text(strip=True)
        if txt and 3 < len(txt) < 200 and "total product life cycle" not in txt.lower():
            return txt
    for h in ["h1", "h2", "h3"]:
        tag = soup.find(h)
        if tag:
            txt = tag.get_text(strip=True)
            if txt and "total product life cycle" not in txt.lower():
                return txt
    return None

def _collect_problem_items(soup: BeautifulSoup, page_url: str, kind: str):
    items: list[ProblemItem] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "cfmaude" not in href.lower():
            continue
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if kind == "device" and "productproblem" not in qs:
            continue
        if kind == "patient" and "patientproblem" not in qs:
            continue
        name = a.get_text(strip=True)
        if not name:
            continue
        count = _row_count_from_anchor(a)
        items.append(ProblemItem(name=name, count=count, maude_link=_abs(page_url, href)))


    seen = set()
    uniq = []
    for it in items:
        if it.name in seen:
            continue
        seen.add(it.name)
        uniq.append(it)
    return uniq

def parse_device_page(html: str, url: str, fallback_name: Optional[str] = None) -> DeviceResult:
    soup = BeautifulSoup(html, "html.parser")
    name = _extract_device_name_from_table(soup) or _extract_device_name_generic(soup) or fallback_name or "Unknown Device"
    device_problems = _collect_problem_items(soup, url, "device")
    patient_problems = _collect_problem_items(soup, url, "patient")
    return DeviceResult(
        device_name=name,
        device_url=url,
        device_problems=device_problems,
        patient_problems=patient_problems,
    )
