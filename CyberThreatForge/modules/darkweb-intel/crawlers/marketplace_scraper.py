"""Dark web marketplace scraper.

Parses listing pages from known markets, extracts product details,
prices, and seller info. Tracks changes over time and categorises
listings into threat-relevant categories.
"""

import asyncio
import json
import logging
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MARKET_CATEGORIES = {
    "credentials": {"credential", "login", "password", "email", "combo", "account"},
    "exploits": {"exploit", "0day", "payload", "rce", "shell", "backdoor"},
    "malware": {"malware", "rat", "trojan", "stealer", "keylogger", "ransomware"},
    "drugs": {"cocaine", "heroin", "mdma", "lsd", "cannabis", "fentanyl"},
    "weapons": {"firearm", "rifle", "pistol", "explosive", "ammo"},
    "docs": {"passport", "id card", "driver license", "scan", "dox"},
    "carding": {"cc", "credit card", "dumps", "track", "cvv", "fullz"},
}

DEFAULT_MARKETS: list[str] = []


@dataclass
class Listing:
    title: str
    url: str
    price: Optional[float] = None
    currency: str = "USD"
    seller: str = "unknown"
    description: str = ""
    category: str = "uncategorised"
    posted: Optional[str] = None
    source_market: str = "unknown"
    first_seen: str = ""
    last_seen: str = ""


@dataclass
class ScanResult:
    monitor_id: str
    listings_scraped: int
    new_products: int
    categories_found: dict[str, int]
    high_risk_items: list[dict[str, Any]]


class MarketplaceScraper:
    """Scrapes known dark-web marketplaces for listings."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._known_listings: dict[str, Listing] = {}
        self._db_path = db_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "marketplace_db.json"
        )
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._load_state()

    def _load_state(self) -> None:
        try:
            if os.path.isfile(self._db_path):
                with open(self._db_path, "r") as f:
                    raw = json.load(f)
                for item in raw:
                    self._known_listings[item["url"]] = Listing(**item)
        except Exception:
            logger.warning("Could not load marketplace DB, starting fresh")

    def _save_state(self) -> None:
        try:
            with open(self._db_path, "w") as f:
                json.dump(
                    [asdict(l) for l in self._known_listings.values()],
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error("Failed to save marketplace DB: %s", e)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, force_close=True)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _categorise(self, title: str, desc: str) -> str:
        text = (title + " " + desc).lower()
        for cat, keywords in MARKET_CATEGORIES.items():
            if any(kw in text for kw in keywords):
                return cat
        return "other"

    def _extract_price(self, text: str) -> Optional[float]:
        patterns = [
            r"\$?([\d,]+\.\d{2})\s*(USD|BTC|XMR)?",
            r"(?:USD|BTC|XMR)\s*\$?([\d,]+\.\d{2})",
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except ValueError:
                    pass
        return None

    async def _parse_listing_page(self, url: str) -> list[Listing]:
        session = await self._get_session()
        listings: list[Listing] = []
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return []

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select(
            "tr, .listing, .product, [class*=listing], [class*=product]"
        )
        if not items:
            items = soup.find_all(["div", "li", "tr"], class_=True)

        now = datetime.now(timezone.utc).isoformat()
        for el in items:
            title_el = el.find(["h2", "h3", "h4", "a", "span", "td"])
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            link_el = el.find("a", href=True)
            href = link_el["href"] if link_el else ""
            if href and not href.startswith("http"):
                href = url.rstrip("/") + "/" + href.lstrip("/")
            desc = el.get_text(" ", strip=True)
            price = self._extract_price(desc)
            seller_el = el.find(
                ["span", "div", "a"],
                class_=re.compile(r"seller|vendor|author", re.I),
            )
            seller = seller_el.get_text(strip=True) if seller_el else "unknown"
            cat = self._categorise(title, desc)

            listing = Listing(
                title=title,
                url=href or url,
                price=price,
                seller=seller,
                description=desc[:500],
                category=cat,
                source_market=url,
                first_seen=now,
                last_seen=now,
            )
            listings.append(listing)
        return listings

    async def scan(
        self,
        markets: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
        max_listings: int = 200,
    ) -> dict[str, Any]:
        targets = markets or DEFAULT_MARKETS
        if not targets:
            return {
                "monitor_id": str(uuid4()),
                "listings_scraped": 0,
                "new_products": 0,
                "categories_found": {},
                "high_risk_items": [],
            }

        all_listings: list[Listing] = []
        for market_url in targets[:5]:
            logger.info("Scanning market: %s", market_url)
            batch = await self._parse_listing_page(market_url)
            all_listings.extend(batch)
            await asyncio.sleep(3.0)

        if categories:
            all_listings = [l for l in all_listings if l.category in categories]

        new_count = 0
        for listing in all_listings[:max_listings]:
            existing = self._known_listings.get(listing.url)
            if existing is None:
                new_count += 1
                self._known_listings[listing.url] = listing
            else:
                existing.last_seen = listing.last_seen
                if listing.price and listing.price != existing.price:
                    logger.info("Price change: %s %.2f -> %.2f", listing.title, existing.price or 0, listing.price)
                    existing.price = listing.price

        self._save_state()

        cat_counts: Counter = Counter(l.category for l in all_listings)
        high_risk = [
            asdict(l)
            for l in all_listings[:max_listings]
            if l.category in ("exploits", "credentials", "malware")
        ]

        return {
            "monitor_id": str(uuid4()),
            "listings_scraped": len(all_listings),
            "new_products": new_count,
            "categories_found": dict(cat_counts),
            "high_risk_items": high_risk[:20],
        }
