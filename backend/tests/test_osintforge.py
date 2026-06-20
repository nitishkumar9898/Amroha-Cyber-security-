import pytest
import asyncio
from app.modules.osint.crawler import crawler
from app.modules.osint.summarizer import summarizer
from app.modules.osint.network_analysis import analyzer
from app.modules.osint.profiling import profiler
from app.modules.osint.misinfo_tracker import tracker
from app.modules.osint.privacy_filter import privacy_filter
from app.modules.osint.darkweb_connector import darkweb_connector
from app.modules.osint.predictive_integration import integrator

@pytest.mark.asyncio
async def test_crawler():
    data = await crawler.fetch_public_data("cyber", "twitter")
    assert len(data) == 2
    assert data[0]["platform"] == "twitter"

@pytest.mark.asyncio
async def test_summarizer():
    texts = ["This is a test tweet about cyber", "Another post about cyber"]
    summary = await summarizer.summarize_texts(texts)
    assert "AI Summary" in summary

@pytest.mark.asyncio
async def test_network_analysis():
    data = [{"author": "user1", "platform": "twitter"}]
    graph = await analyzer.build_interaction_graph(data)
    assert len(graph["nodes"]) == 1
    assert graph["nodes"][0]["id"] == "user1"

@pytest.mark.asyncio
async def test_profiling():
    profile = await profiler.profile_actor("user1", {"post_count": 150})
    assert profile["bot_likelihood"] == "High"

@pytest.mark.asyncio
async def test_misinfo_tracker():
    res = await tracker.detect_misinformation("This is a totally fake conspiracy.")
    assert res["misinfo_probability"] > 0.5

def test_privacy_filter():
    filtered = privacy_filter.anonymize_text("Contact me at test@example.com")
    assert "test@example.com" not in filtered
    assert "[EMAIL_REDACTED]" in filtered

@pytest.mark.asyncio
async def test_darkweb_connector():
    await darkweb_connector.connect()
    assert darkweb_connector.connected
    res = await darkweb_connector.search_forums("exploit")
    assert len(res) == 1

@pytest.mark.asyncio
async def test_predictive_integration():
    res = await integrator.feed_intelligence("OSINT", "found a new exploit")
    assert res["predictive_impact_score"] > 0.7
