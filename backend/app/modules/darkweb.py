"""
Dark Web Threat Intelligence Parser & Crawler Simulator
Implements ethical onion index crawling, leaked database classification,
cryptocurrency wallet extraction, and threat actor profiling based on metadata.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List

class DarkwebIntelligence:
    @staticmethod
    def parse_scraped_intel(filepath: str) -> Dict[str, Any]:
        """
        Parses raw scraped dark web intel dumps.
        If file doesn't exist, returns empty structure.
        """
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def crawl_onion_index(query: str) -> List[Dict[str, Any]]:
        """
        Simulates ethical crawling of Tor onion directories.
        Extracts listings matching the query and tags them by category.
        """
        seed_hash = int(hashlib.sha256(query.encode()).hexdigest(), 16)
        
        # Match keywords to mock realistic search outputs
        query_l = query.lower()
        
        matches = []
        if any(w in query_l for w in ["database", "leak", "dump", "cbi", "credentials"]):
            matches.append({
                "onion_url": f"http://leakdb{seed_hash % 99}onion.onion",
                "title": "Exposed Government Credentials database dump",
                "category": "CREDENTIAL_LEAK",
                "date_published": "2026-06-18",
                "body_content": "Exposing 12,000 corporate credentials and internal emails. Format: email:hash:salt.",
                "severity": "HIGH"
            })
            
        if any(w in query_l for w in ["exploit", "zero-day", "payload", "bypass", "c2"]):
            matches.append({
                "onion_url": f"http://exploitmarket{seed_hash % 99}.onion",
                "title": "Windows Local Privilege Escalation Zero-Day",
                "category": "EXPLOIT_MARKET",
                "date_published": "2026-06-19",
                "body_content": "Selling zero-day vulnerability in win32k.sys. Price: 1.5 BTC. Escrow only.",
                "severity": "CRITICAL"
            })
            
        if not matches:
            matches.append({
                "onion_url": f"http://generalforum{seed_hash % 99}.onion",
                "title": "General discussion on threat modeling",
                "category": "FORUM_THREAD",
                "date_published": "2026-06-15",
                "body_content": "Discussion thread discussing best practices in sandboxing software execution.",
                "severity": "LOW"
            })
            
        return matches

    @staticmethod
    def profile_threat_actor(handle: str, post_timestamps: List[str]) -> Dict[str, Any]:
        """
        Correlates threat actor metadata: active times (timezone fingerprinting),
        crypto wallet addresses, PGP keys, and estimated operational location.
        """
        seed_hash = int(hashlib.md5(handle.encode()).hexdigest(), 16)
        
        # Estimate timezone based on post timestamp hours
        hours = []
        for ts in post_timestamps:
            try:
                # Expected format: "YYYY-MM-DD HH:MM:SS"
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                hours.append(dt.hour)
            except Exception:
                # Default hours range fallback
                hours.extend([10, 11, 14, 16])
                
        avg_hour = sum(hours) / len(hours) if hours else 12.0
        
        # Map avg hour to likely timezone (UTC+3, UTC+8, etc.)
        if 8 <= avg_hour <= 16:
            estimated_timezone = "UTC+3 (Eastern Europe / Moscow)"
            operates_at_night = False
        else:
            estimated_timezone = "UTC+8 (East Asia)"
            operates_at_night = True
            
        btc_wallet = f"1FeexV6bAH2S8ye{seed_hash % 99999}xK5111"
        xmr_wallet = f"44AFFq5kSiGb{seed_hash % 9999}x44"
        
        pgp_fingerprint = f"PGP_KEY_{hashlib.sha1(handle.encode()).hexdigest()[:16].upper()}"
        
        return {
            "actor_handle": handle,
            "pgp_fingerprint": pgp_fingerprint,
            "estimated_timezone": estimated_timezone,
            "nighttime_activity_flag": operates_at_night,
            "cryptocurrency_wallets": {
                "bitcoin_wallet": btc_wallet,
                "monero_wallet": xmr_wallet
            },
            "threat_actor_class": "APT_State_Sponsored" if (seed_hash % 2 == 0) else "Ransomware_Affiliate"
        }
