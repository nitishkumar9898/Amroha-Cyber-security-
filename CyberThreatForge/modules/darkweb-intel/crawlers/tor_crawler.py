"""TOR / I2P hidden-service crawler.

Handles SOCKS5 proxy connections, text extraction, link discovery,
optional headless-screenshot capture, and configurable rate-limiting.
"""

import asyncio
import hashlib
import logging
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin, urlparse
from uuid import uuid4

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TOR_SOCKS5 = "socks5://127.0.0.1:9050"
I2P_SOCKS = "socks5://127.0.0.1:9050"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=60)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0"
)


@dataclass
class CrawlConfig:
    delay: float = 2.0
    max_pages: int = 10
    max_depth: int = 3
    same_domain_only: bool = True
    strip_pii: bool = True
    take_screenshot: bool = False
    proxy: str = TOR_SOCKS5


@dataclass
class PageResult:
    url: str
    status: int
    title: str = ""
    text: str = ""
    links: list[str] = field(default_factory=list)
    error: Optional[str] = None


class TorCrawler:
    """Async crawler for .onion / .i2p hidden services."""

    def __init__(self, config: Optional[CrawlConfig] = None) -> None:
        self.config = config or CrawlConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._visited: set[str] = set()
        self._semaphore = asyncio.Semaphore(5)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, force_close=True)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _resolve_links(self, base: str, soup: BeautifulSoup) -> list[str]:
        links: list[str] = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            absolute = urljoin(base, href)
            parsed = urlparse(absolute)
            if parsed.scheme in ("http", "https"):
                links.append(absolute)
        return links

    def _extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for elem in soup.find_all(["script", "style", "nav", "footer"]):
            elem.decompose()
        text = soup.get_text(separator="\n", strip=True)
        if self.config.strip_pii:
            text = self._strip_pii(text)
        return text

    def _strip_pii(self, text: str) -> str:
        patterns = [
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),
            (r"\b(?:\d{3}[-.]?){2}\d{4}\b", "[PHONE]"),
            (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
            (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b", "[CC]"),
        ]
        for pat, repl in patterns:
            text = re.sub(pat, repl, text)
        return text

    async def _fetch_page(self, url: str) -> PageResult:
        session = await self._get_session()
        result = PageResult(url=url, status=0)
        try:
            async with self._semaphore:
                async with session.get(
                    url,
                    proxy=self.config.proxy,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                ) as resp:
                    result.status = resp.status
                    if resp.status != 200:
                        result.error = f"HTTP {resp.status}"
                        return result
                    html = await resp.text(encoding="utf-8", errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            result.title = title_tag.get_text(strip=True) if title_tag else ""
            result.text = self._extract_text(html)
            result.links = self._resolve_links(url, soup)
        except asyncio.TimeoutError:
            result.error = "timeout"
        except aiohttp.ClientError as exc:
            result.error = str(exc)
        except Exception as exc:
            result.error = f"unexpected: {exc}"
            logger.warning("Fetch error for %s: %s", url, result.error)
        return result

    async def _maybe_screenshot(self, url: str) -> Optional[str]:
        if not self.config.take_screenshot:
            return None
        try:
            tmp = tempfile.NamedTemporaryFile(
                prefix="dw_screenshot_", suffix=".png", delete=False
            )
            path = tmp.name
            tmp.close()
            cmd = [
                "wkhtmltoimage",
                "--proxy",
                self.config.proxy,
                url,
                path,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=30)
            return path if os.path.isfile(path) else None
        except Exception:
            logger.exception("Screenshot failed for %s", url)
            return None

    async def crawl(
        self,
        url: str,
        max_pages: int = 10,
        delay: float = 2.0,
        screenshot: bool = False,
        proxy: Optional[str] = None,
    ) -> dict[str, Any]:
        self._visited.clear()
        if proxy:
            self.config.proxy = proxy
        self.config.max_pages = max_pages
        self.config.delay = delay
        self.config.take_screenshot = screenshot

        queue: list[str] = [url]
        pages: list[PageResult] = []
        crawl_id = str(uuid4())

        while queue and len(pages) < self.config.max_pages:
            current = queue.pop(0)
            if current in self._visited:
                continue
            self._visited.add(current)

            logger.info("Crawling [%d/%d]: %s", len(pages) + 1, max_pages, current)
            page = await self._fetch_page(current)
            pages.append(page)

            if page.error is None:
                for link in page.links:
                    if (
                        link not in self._visited
                        and link not in queue
                        and len(pages) + len(queue) < max_pages
                    ):
                        if self.config.same_domain_only:
                            if urlparse(link).netloc == urlparse(url).netloc:
                                queue.append(link)
                        else:
                            queue.append(link)

            await asyncio.sleep(self.config.delay)

        screenshot_path = None
        if screenshot and pages:
            screenshot_path = await self._maybe_screenshot(url)

        coc = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step": "crawl_complete",
                "pages_fetched": len(pages),
                "urls_visited": len(self._visited),
            }
        ]

        all_text = "\n".join(p.text for p in pages if p.text)
        return {
            "crawl_id": crawl_id,
            "url": url,
            "status": pages[0].status if pages else 0,
            "title": pages[0].title if pages else "",
            "text_length": len(all_text),
            "links_found": sum(len(p.links) for p in pages),
            "pages_crawled": len(pages),
            "screenshot_path": screenshot_path,
            "chain_of_custody": coc,
        }
