import hashlib
import networkx as nx
from typing import List, Dict, Any, Tuple

def detect_stealthy_persistence(scan_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simulates heuristics and machine learning checks for advanced stealth persistence.
    """
    detected_artifacts = []
    
    # Simple heuristics mapping common stealth patterns
    for item in scan_data:
        artifact_type = item.get("type", "unknown").lower()
        value = item.get("value", "")
        
        stealth_score = 0.0
        
        # Simulated persistence indicators
        if artifact_type == "registry" and "Run" in value:
            stealth_score = 0.4
        elif artifact_type == "wmi" and "EventConsumer" in value:
            stealth_score = 0.85
        elif artifact_type == "scheduled_task" and "System" in value:
            stealth_score = 0.6
        elif artifact_type == "bcedit":
            stealth_score = 0.9 # High stealth bootkit indicator
            
        if stealth_score > 0.3:
            detected_artifacts.append({
                "artifact_type": artifact_type,
                "artifact_value": value,
                "stealth_score": stealth_score
            })
            
    return detected_artifacts

def map_ttps_gnn(artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simulates a Graph Neural Network clustering to map artifacts to MITRE ATT&CK TTPs.
    Constructs a NetworkX graph and runs community detection/heuristics.
    """
    G = nx.Graph()
    
    # Add artifacts as nodes
    for i, art in enumerate(artifacts):
        node_id = f"art_{i}"
        G.add_node(node_id, **art)
        
    # Simulated connections based on similar scores/types
    for i in range(len(artifacts)):
        for j in range(i + 1, len(artifacts)):
            if artifacts[i]["stealth_score"] >= 0.8 and artifacts[j]["stealth_score"] >= 0.8:
                G.add_edge(f"art_{i}", f"art_{j}", weight=0.9)
            elif artifacts[i]["artifact_type"] == artifacts[j]["artifact_type"]:
                G.add_edge(f"art_{i}", f"art_{j}", weight=0.5)

    # Simulated GNN prediction mapping to TTPs based on graph properties
    ttp_mappings = []
    for node, data in G.nodes(data=True):
        degree = G.degree(node)
        
        # Mock mapping logic based on degree and stealth_score
        technique_id = "T1059" # Default fallback
        technique_name = "Command and Scripting Interpreter"
        score = data.get("stealth_score", 0.0)
        
        if data.get("artifact_type") == "registry":
            technique_id = "T1547.001"
            technique_name = "Registry Run Keys / Startup Folder"
        elif data.get("artifact_type") == "wmi":
            technique_id = "T1546.003"
            technique_name = "Windows Management Instrumentation Event Subscription"
        
        ttp_mappings.append({
            "technique_id": technique_id,
            "technique_name": technique_name,
            "graph_node_id": node,
            "detection_score": min(1.0, score + (degree * 0.1))
        })
        
    return ttp_mappings

def reconstruct_campaign(ttp_mappings: List[Dict[str, Any]]) -> Tuple[str, int, float]:
    """
    Analyzes sequence and overlaps to reconstruct a campaign.
    Returns: campaign_name, mock_threat_actor_id, attribution_confidence
    """
    if not ttp_mappings:
        return "Unknown Campaign", None, 0.0
        
    # Simple logic to simulate attribution
    avg_score = sum(t["detection_score"] for t in ttp_mappings) / len(ttp_mappings)
    
    campaign_name = f"Op-Graphite-{hashlib.md5(str(avg_score).encode()).hexdigest()[:6]}"
    
    # Mock Attribution: if wmi is heavily used, maybe APT29
    has_wmi = any(t["technique_id"] == "T1546.003" for t in ttp_mappings)
    threat_actor_id = 1 if has_wmi else 2
    
    confidence = min(0.95, avg_score + 0.1)
    
    return campaign_name, threat_actor_id, confidence
