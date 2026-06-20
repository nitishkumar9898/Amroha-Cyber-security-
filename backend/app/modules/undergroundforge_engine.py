from typing import Dict, Any

def simulate_darkweb_scrape(marketplace_url: str, keyword: str) -> Dict[str, Any]:
    """
    Simulates scraping an underground marketplace for a specific keyword.
    """
    context = f"Found '{keyword}' mentioned in vendor listing selling 0-day exploits for SCADA systems."
    threat = 0.95 if "0-day" in context or "exploit" in keyword.lower() else 0.60
    
    return {
        "marketplace": marketplace_url,
        "keyword": keyword,
        "match_context": context,
        "threat_level": threat
    }
