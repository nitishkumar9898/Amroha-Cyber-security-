import hashlib
import random
from typing import Dict, Any, List

def track_propagation(media_url: str, target: str) -> Dict[str, Any]:
    """
    Simulates OSINT/Misinformation scraping to track the spread of a payload.
    """
    # Create a deterministic mock hash based on the URL
    payload_hash = hashlib.sha256(media_url.encode()).hexdigest()[:16]
    
    platforms = ["Twitter", "Telegram", "Reddit", "Facebook", "TikTok"]
    # Randomly select 2 to 4 platforms
    affected = random.sample(platforms, k=random.randint(2, 4))
    
    return {
        "campaign_name": f"Op-{target.replace(' ', '')}-{payload_hash[:4]}",
        "target_entity": target,
        "payload_hash": payload_hash,
        "platforms_affected": affected
    }

def detect_bot_amplification(campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates a mock graph of bot nodes responsible for amplification.
    """
    nodes = []
    platforms = campaign_data.get("platforms_affected", ["Twitter"])
    
    # 1 Origin Node per platform
    for plat in platforms:
        nodes.append({
            "node_id": f"origin_{plat.lower()}_{random.randint(1000,9999)}",
            "node_type": "origin",
            "platform": plat,
            "engagement_score": round(random.uniform(0.8, 1.0), 2)
        })
        
        # 3 to 6 amplifier bots per origin
        for _ in range(random.randint(3, 6)):
            nodes.append({
                "node_id": f"bot_{plat.lower()}_{random.randint(10000,99999)}",
                "node_type": "amplifier",
                "platform": plat,
                "engagement_score": round(random.uniform(0.1, 0.5), 2)
            })
            
    # Maybe 1 or 2 bridge nodes connecting platforms
    if len(platforms) > 1:
        for _ in range(random.randint(1, 2)):
            nodes.append({
                "node_id": f"bridge_{random.randint(1000,9999)}",
                "node_type": "bridge",
                "platform": "CrossPlatform",
                "engagement_score": round(random.uniform(0.6, 0.9), 2)
            })
            
    return nodes

def assess_impact(campaign_data: Dict[str, Any], bot_count: int) -> Dict[str, Any]:
    """
    Calculates the simulated impact on public opinion.
    """
    # Drift from -1.0 (extreme negative shift) to 1.0
    drift = round(random.uniform(-0.8, -0.2), 2) 
    reach = bot_count * random.randint(1500, 5000)
    
    # Impact score between 0.0 and 1.0
    score = min(1.0, (abs(drift) * 0.5) + (min(reach, 100000) / 100000 * 0.5))
    
    return {
        "sentiment_drift": drift,
        "reach_estimate": reach,
        "impact_score": round(score, 2)
    }

def generate_takedown_recommendations(campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates automated takedown requests based on platform policies.
    """
    recommendations = []
    for plat in campaign_data.get("platforms_affected", []):
        policy = "Manipulated Media & Synthetic Content Policy"
        if plat == "Twitter":
            policy = "Synthetic and Manipulated Media Policy"
        elif plat == "Facebook":
            policy = "Community Standards: Manipulated Media"
            
        recommendations.append({
            "platform": plat,
            "policy_violation": policy,
            "evidence_summary": f"Coordinated inauthentic behavior detected propagating payload {campaign_data.get('payload_hash')}.",
            "status": "Draft"
        })
    return recommendations
