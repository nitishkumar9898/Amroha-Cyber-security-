"""Dark Web + Federated Intelligence Module — FastAPI Application.

TOR/I2P monitoring, breach data tracking, marketplace scraping,
ransomware leak tracking, and actor profiling via a unified API.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

import aiohttp
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from crawlers.tor_crawler import TorCrawler
from crawlers.marketplace_scraper import MarketplaceScraper
from crawlers.ransomware_tracker import RansomwareTracker
from crawlers.breach_monitor import BreachMonitor
from models.actor_profiler import ActorProfiler
from models.threat_classifier import ThreatClassifier

logger = logging.getLogger("darkweb_intel")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="CyberThreatForge — Dark Web Intelligence",
    version="1.0.0",
    description="Federated dark-web intelligence gathering & threat analysis",
)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CrawlRequest(BaseModel):
    url: str = Field(..., description="Target .onion or .i2p URL")
    max_pages: int = Field(10, ge=1, le=500)
    delay: float = Field(2.0, ge=0.1, le=30.0)
    screenshot: bool = False


class CrawlResult(BaseModel):
    crawl_id: str
    url: str
    status: int
    title: Optional[str] = None
    text_length: int = 0
    links_found: int = 0
    pages_crawled: int = 0
    screenshot_path: Optional[str] = None
    chain_of_custody: list[dict[str, Any]] = []


class BreachCheckRequest(BaseModel):
    emails: list[str] = Field(default_factory=list, max_length=100)
    domains: list[str] = Field(default_factory=list, max_length=50)
    check_pwned: bool = True
    check_custom_db: bool = True


class BreachCheckResult(BaseModel):
    query_id: str
    emails_checked: int
    domains_checked: int
    breaches_found: list[dict[str, Any]] = []
    credentials_exposed: int = 0
    risk_score: float = 0.0


class MarketplaceMonitorRequest(BaseModel):
    markets: list[str] = Field(default_factory=list, description="Market URLs")
    categories: list[str] = Field(default_factory=list)
    max_listings: int = 200


class MarketplaceMonitorResult(BaseModel):
    monitor_id: str
    listings_scraped: int
    new_products: int = 0
    categories_found: dict[str, int] = {}
    high_risk_items: list[dict[str, Any]] = []


class ActorProfileRequest(BaseModel):
    forum_posts: list[str] = Field(..., min_length=1, max_length=500)
    usernames: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)


class ActorProfileResult(BaseModel):
    profile_id: str
    actor_name: Optional[str] = None
    confidence: float = 0.0
    stylometry: dict[str, Any] = {}
    topics: list[str] = []
    sentiment: str = "neutral"
    risk_score: float = 0.0
    reputation_score: float = 0.0
    correlated_usernames: list[str] = []


class ThreatAnalysisRequest(BaseModel):
    indicators: list[str] = Field(..., description="IPs, domains, hashes")
    context: Optional[str] = None


class ThreatAnalysisResult(BaseModel):
    analysis_id: str
    threat_score: float = 0.0
    mitre_techniques: list[str] = []
    severity: str = "unknown"
    enriched_indicators: list[dict[str, Any]] = []
    false_positive: bool = False


class RansomwareTrackRequest(BaseModel):
    groups: list[str] = Field(default_factory=list)
    refresh: bool = False


class RansomwareTrackResult(BaseModel):
    track_id: str
    groups_monitored: int = 0
    victims_new: int = 0
    victims: list[dict[str, Any]] = []
    sensitivity_analysis: dict[str, int] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_coc(step: str, detail: str) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "detail": detail,
        "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
    }


def _strip_pii(text: str) -> str:
    patterns = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),
        (r"\b(?:\d{3}[-.]?){2}\d{4}\b", "[PHONE]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b", "[CC]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


# ---------------------------------------------------------------------------
# FastAPI event handlers and endpoints
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup():
    app.state.tor_crawler = TorCrawler()
    app.state.market_scraper = MarketplaceScraper()
    app.state.ransomware_tracker = RansomwareTracker()
    app.state.breach_monitor = BreachMonitor()
    app.state.actor_profiler = ActorProfiler()
    app.state.threat_classifier = ThreatClassifier()
    logger.info("DarkWeb-Intel module initialised.")


@app.on_event("shutdown")
async def shutdown():
    await app.state.tor_crawler.close()
    await app.state.breach_monitor.close()
    logger.info("DarkWeb-Intel module shut down.")


@app.get("/health")
async def health():
    return {"status": "ok", "module": "darkweb-intel", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/crawl/tor", response_model=CrawlResult)
async def crawl_tor(req: CrawlRequest):
    coc: list[dict[str, Any]] = []
    if not req.url.endswith(".onion"):
        raise HTTPException(400, "URL must be a .onion address")
    coc.append(_make_coc("validate", f"Validated .onion URL: {req.url}"))
    crawler: TorCrawler = app.state.tor_crawler
    try:
        result = await crawler.crawl(
            url=req.url,
            max_pages=req.max_pages,
            delay=req.delay,
            screenshot=req.screenshot,
        )
    except Exception as exc:
        logger.exception("TOR crawl failed")
        raise HTTPException(502, f"Crawl failed: {exc}")
    result["chain_of_custody"] = coc + result.get("chain_of_custody", [])
    return CrawlResult(**result)


@app.post("/crawl/i2p", response_model=CrawlResult)
async def crawl_i2p(req: CrawlRequest):
    coc: list[dict[str, Any]] = []
    if not req.url.endswith(".i2p"):
        raise HTTPException(400, "URL must be a .i2p address")
    coc.append(_make_coc("validate", f"Validated .i2p URL: {req.url}"))
    crawler: TorCrawler = app.state.tor_crawler
    try:
        result = await crawler.crawl(
            url=req.url,
            max_pages=req.max_pages,
            delay=req.delay,
            screenshot=req.screenshot,
            proxy="http://127.0.0.1:4444",
        )
    except Exception as exc:
        logger.exception("I2P crawl failed")
        raise HTTPException(502, f"I2P crawl failed: {exc}")
    result["chain_of_custody"] = coc + result.get("chain_of_custody", [])
    return CrawlResult(**result)


@app.post("/monitor/breaches", response_model=BreachCheckResult)
async def check_breaches(req: BreachCheckRequest):
    monitor: BreachMonitor = app.state.breach_monitor
    try:
        result = await monitor.check(
            emails=req.emails,
            domains=req.domains,
            check_pwned=req.check_pwned,
            check_custom_db=req.check_custom_db,
        )
    except Exception as exc:
        logger.exception("Breach check failed")
        raise HTTPException(502, f"Breach check failed: {exc}")
    return BreachCheckResult(**result)


@app.post("/monitor/marketplace", response_model=MarketplaceMonitorResult)
async def monitor_marketplace(req: MarketplaceMonitorRequest):
    scraper: MarketplaceScraper = app.state.market_scraper
    try:
        result = await scraper.scan(
            markets=req.markets,
            categories=req.categories,
            max_listings=req.max_listings,
        )
    except Exception as exc:
        logger.exception("Marketplace scan failed")
        raise HTTPException(502, f"Marketplace scan failed: {exc}")
    return MarketplaceMonitorResult(**result)


@app.post("/analyze/actor", response_model=ActorProfileResult)
async def analyze_actor(req: ActorProfileRequest):
    profiler: ActorProfiler = app.state.actor_profiler
    try:
        result = await profiler.profile(
            posts=req.forum_posts,
            usernames=req.usernames,
            platforms=req.platforms,
        )
    except Exception as exc:
        logger.exception("Actor profiling failed")
        raise HTTPException(500, f"Actor profiling failed: {exc}")
    return ActorProfileResult(**result)


@app.post("/analyze/threat", response_model=ThreatAnalysisResult)
async def analyze_threat(req: ThreatAnalysisRequest):
    classifier: ThreatClassifier = app.state.threat_classifier
    try:
        result = await classifier.analyze(
            indicators=req.indicators,
            context=req.context,
        )
    except Exception as exc:
        logger.exception("Threat analysis failed")
        raise HTTPException(500, f"Threat analysis failed: {exc}")
    return ThreatAnalysisResult(**result)


@app.post("/track/ransomware", response_model=RansomwareTrackResult)
async def track_ransomware(req: RansomwareTrackRequest):
    tracker: RansomwareTracker = app.state.ransomware_tracker
    try:
        result = await tracker.track(
            groups=req.groups,
            refresh=req.refresh,
        )
    except Exception as exc:
        logger.exception("Ransomware tracking failed")
        raise HTTPException(502, f"Ransomware tracking failed: {exc}")
    return RansomwareTrackResult(**result)
