import asyncio
import hashlib
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiohttp

logger = logging.getLogger("social_collector")


@dataclass
class SocialPost:
    platform: str
    platform_id: str
    content: str
    author: str
    author_id: str
    timestamp: str
    url: str
    engagement: dict[str, int] = field(default_factory=lambda: {"likes": 0, "replies": 0, "shares": 0})
    metadata: dict[str, Any] = field(default_factory=dict)
    chain_of_custody: list[dict[str, Any]] = field(default_factory=list)
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SocialProfile:
    platform: str
    username: str
    display_name: str
    bio: str
    avatar_url: str
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    account_created: str = ""
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    chain_of_custody: list[dict[str, Any]] = field(default_factory=list)


class BaseSocialCollector(ABC):
    def __init__(self, platform: str, rate_limit: float = 1.0):
        self.platform = platform
        self.rate_limit = rate_limit
        self._last_call: float = 0.0

    async def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self._last_call = time.time()

    def _make_coc(self, step: str, detail: str) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "detail": detail,
            "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
        }

    @abstractmethod
    async def search(self, query: str, limit: int = 50) -> list[SocialPost]: ...

    @abstractmethod
    async def get_profile(self, username: str) -> Optional[SocialProfile]: ...

    @abstractmethod
    async def get_timeline(self, username: str, limit: int = 50) -> list[SocialPost]: ...


class TwitterCollector(BaseSocialCollector):
    def __init__(self, rate_limit: float = 1.0):
        super().__init__("twitter", rate_limit)
        self.base_url = "https://api.twitter.com/2"

    async def search(self, query: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("search", f"Twitter search: {query[:100]}")]
        posts = []
        for i in range(min(limit, 20)):
            posts.append(SocialPost(
                platform="twitter",
                platform_id=f"tw_sim_{uuid4().hex[:12]}",
                content=f"Simulated tweet {i+1}: {query[:50]} — trending discussion on this topic.",
                author=f"user_{hash(query)%10000:04d}",
                author_id=f"uid_{uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://twitter.com/user_{i}/status/{uuid4().hex[:12]}",
                engagement={"likes": hash(query) % 500, "replies": hash(query) % 50, "shares": hash(query) % 100},
                metadata={"hashtags": [f"#{w}" for w in query.split() if len(w) > 3][:5]},
                chain_of_custody=coc,
            ))
        logger.info("Twitter search returned %d simulated results", len(posts))
        return posts

    async def get_profile(self, username: str) -> Optional[SocialProfile]:
        await self._throttle()
        coc = [self._make_coc("profile", f"Twitter profile: {username}")]
        return SocialProfile(
            platform="twitter",
            username=username,
            display_name=username.title(),
            bio=f"Simulated bio for {username} — interests in technology and cybersecurity.",
            avatar_url=f"https://pbs.twimg.com/profile_images/{uuid4().hex[:16]}.jpg",
            follower_count=hash(username) % 50000,
            following_count=hash(username) % 2000,
            post_count=hash(username) % 5000,
            account_created="2020-01-15T00:00:00Z",
            verified=hash(username) % 10 == 0,
            chain_of_custody=coc,
        )

    async def get_timeline(self, username: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("timeline", f"Twitter timeline: {username}")]
        return [
            SocialPost(
                platform="twitter",
                platform_id=f"tw_tl_{uuid4().hex[:12]}",
                content=f"Simulated timeline post {i+1} from {username}.",
                author=username,
                author_id=f"uid_{uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://twitter.com/{username}/status/{uuid4().hex[:12]}",
                chain_of_custody=coc,
            )
            for i in range(min(limit, 20))
        ]


class RedditCollector(BaseSocialCollector):
    def __init__(self, rate_limit: float = 2.0):
        super().__init__("reddit", rate_limit)
        self.base_url = "https://oauth.reddit.com"

    async def search(self, query: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("search", f"Reddit search: {query[:100]}")]
        posts = []
        for i in range(min(limit, 20)):
            posts.append(SocialPost(
                platform="reddit",
                platform_id=f"rd_{uuid4().hex[:10]}",
                content=f"Simulated Reddit post #{i+1}: Discussing '{query[:50]}' in r/cybersecurity.",
                author=f"redditor_{hash(query)%5000:04d}",
                author_id=f"rd_uid_{uuid4().hex[:10]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://reddit.com/r/cybersecurity/comments/{uuid4().hex[:10]}/",
                engagement={"likes": hash(query) % 2000, "replies": hash(query) % 300, "shares": 0},
                metadata={"subreddit": "cybersecurity", "score": hash(query) % 1000},
                chain_of_custody=coc,
            ))
        return posts

    async def get_profile(self, username: str) -> Optional[SocialProfile]:
        await self._throttle()
        coc = [self._make_coc("profile", f"Reddit profile: {username}")]
        return SocialProfile(
            platform="reddit",
            username=username,
            display_name=f"u/{username}",
            bio=f"Reddit user active in cybersecurity and OSINT communities.",
            avatar_url="",
            follower_count=hash(username) % 5000,
            following_count=0,
            post_count=hash(username) % 2000,
            account_created="2019-06-01T00:00:00Z",
            verified=False,
            chain_of_custody=coc,
        )

    async def get_timeline(self, username: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("timeline", f"Reddit activity: {username}")]
        return [
            SocialPost(
                platform="reddit",
                platform_id=f"rd_tl_{uuid4().hex[:10]}",
                content=f"Simulated comment by {username} on r/cybersecurity.",
                author=username,
                author_id=f"rd_uid_{uuid4().hex[:10]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://reddit.com/r/cybersecurity/comments/{uuid4().hex[:10]}/",
                engagement={"likes": hash(username) % 500, "replies": 0, "shares": 0},
                metadata={"subreddit": "cybersecurity", "comment": True},
                chain_of_custody=coc,
            )
            for i in range(min(limit, 20))
        ]


class TelegramCollector(BaseSocialCollector):
    def __init__(self, rate_limit: float = 1.5):
        super().__init__("telegram", rate_limit)
        self.base_url = "https://api.telegram.org"

    async def search(self, query: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("search", f"Telegram search: {query[:100]}")]
        return [
            SocialPost(
                platform="telegram",
                platform_id=f"tg_{uuid4().hex[:10]}",
                content=f"Simulated Telegram message about '{query[:50]}' from channel 'CyberIntelAlert'.",
                author=f"channel_{hash(query)%100:03d}",
                author_id=f"tg_ch_{uuid4().hex[:10]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://t.me/cyberintelalert/{1000+i}",
                engagement={"likes": hash(query) % 100, "replies": 0, "shares": hash(query) % 50},
                metadata={"channel": "CyberIntelAlert", "forwarded": hash(query) % 3 == 0},
                chain_of_custody=coc,
            )
            for i in range(min(limit, 20))
        ]

    async def get_profile(self, username: str) -> Optional[SocialProfile]:
        await self._throttle()
        coc = [self._make_coc("profile", f"Telegram channel: {username}")]
        return SocialProfile(
            platform="telegram",
            username=username,
            display_name=username,
            bio="Telegram channel for cybersecurity intelligence sharing.",
            avatar_url="",
            follower_count=hash(username) % 100000,
            following_count=0,
            post_count=hash(username) % 5000,
            account_created="2021-01-01T00:00:00Z",
            verified=hash(username) % 20 == 0,
            chain_of_custody=coc,
        )

    async def get_timeline(self, username: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("timeline", f"Telegram channel messages: {username}")]
        return [
            SocialPost(
                platform="telegram",
                platform_id=f"tg_tl_{uuid4().hex[:10]}",
                content=f"Simulated message #{i+1} from channel @{username}.",
                author=username,
                author_id=f"tg_ch_{uuid4().hex[:10]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://t.me/{username}/{i+1}",
                chain_of_custody=coc,
            )
            for i in range(min(limit, 20))
        ]


class DiscordCollector(BaseSocialCollector):
    def __init__(self, rate_limit: float = 1.0):
        super().__init__("discord", rate_limit)
        self.base_url = "https://discord.com/api/v9"

    async def search(self, query: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("search", f"Discord search: {query[:100]}")]
        return [
            SocialPost(
                platform="discord",
                platform_id=f"dc_{uuid4().hex[:10]}",
                content=f"Simulated Discord message about '{query[:50]}' from #cyber-threats channel.",
                author=f"user_{hash(query+i)%10000:04d}",
                author_id=f"dc_uid_{uuid4().hex[:10]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://discord.com/channels/12345/67890/{uuid4().hex[:16]}",
                engagement={"likes": 0, "replies": hash(query) % 20, "shares": 0},
                metadata={"server": "CyberSec Hub", "channel": "cyber-threats", "message_type": "default"},
                chain_of_custody=coc,
            )
            for i in range(min(limit, 20))
        ]

    async def get_profile(self, username: str) -> Optional[SocialProfile]:
        await self._throttle()
        coc = [self._make_coc("profile", f"Discord user: {username}")]
        return SocialProfile(
            platform="discord",
            username=username,
            display_name=username,
            bio="Discord user in cybersecurity communities.",
            avatar_url=f"https://cdn.discordapp.com/avatars/{uuid4().hex[:16]}/{uuid4().hex[:16]}.png",
            follower_count=0,
            following_count=0,
            post_count=hash(username) % 5000,
            account_created="2020-03-10T00:00:00Z",
            verified=False,
            chain_of_custody=coc,
        )

    async def get_timeline(self, username: str, limit: int = 50) -> list[SocialPost]:
        await self._throttle()
        coc = [self._make_coc("timeline", f"Discord messages by: {username}")]
        return [
            SocialPost(
                platform="discord",
                platform_id=f"dc_tl_{uuid4().hex[:10]}",
                content=f"Simulated Discord message #{i+1} from {username} in #general.",
                author=username,
                author_id=f"dc_uid_{uuid4().hex[:10]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                url=f"https://discord.com/channels/12345/67890/{uuid4().hex[:16]}",
                metadata={"server": "CyberSec Hub", "channel": "general"},
                chain_of_custody=coc,
            )
            for i in range(min(limit, 20))
        ]


class SocialMediaCollector:
    def __init__(self):
        self.collectors: dict[str, BaseSocialCollector] = {
            "twitter": TwitterCollector(),
            "reddit": RedditCollector(),
            "telegram": TelegramCollector(),
            "discord": DiscordCollector(),
        }

    async def collect(
        self,
        platforms: list[str],
        query: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        coc: list[dict[str, Any]] = []
        coc.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "init",
            "detail": f"Social media collection for: {query[:100]} on {platforms}",
            "handler_id": hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16],
        })
        results: dict[str, Any] = {
            "collection_id": uuid4().hex[:16],
            "query": query,
            "platforms": {},
            "total_posts": 0,
            "chain_of_custody": coc,
        }
        for platform in platforms:
            p = platform.lower()
            collector = self.collectors.get(p)
            if not collector:
                results["platforms"][p] = {"error": f"No collector for {p}"}
                continue
            try:
                posts = await collector.search(query, limit)
                serialized = [asdict(post) for post in posts]
                for s in serialized:
                    s["collected_at"] = datetime.now(timezone.utc).isoformat()
                results["platforms"][p] = {
                    "posts_count": len(posts),
                    "posts": serialized,
                }
                results["total_posts"] += len(posts)
            except Exception as exc:
                logger.exception("Collection failed for %s", p)
                results["platforms"][p] = {"error": str(exc)}
        return results

    async def get_profile(self, platform: str, username: str) -> Optional[SocialProfile]:
        collector = self.collectors.get(platform.lower())
        if not collector:
            return None
        return await collector.get_profile(username)

    async def get_timeline(self, platform: str, username: str, limit: int = 50) -> list[SocialPost]:
        collector = self.collectors.get(platform.lower())
        if not collector:
            return []
        return await collector.get_timeline(username, limit)
