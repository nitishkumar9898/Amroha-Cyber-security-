from typing import Dict, Any

def run_correlation(source: str, target: str) -> Dict[str, Any]:
    """
    Simulates graph-based evidence correlation between modules.
    """
    confidence = 0.85 if source != target else 1.0
    
    nodes = [
        {"id": "n1", "label": f"{source} Evidence", "type": "evidence"},
        {"id": "n2", "label": f"{target} Indicator", "type": "indicator"},
        {"id": "n3", "label": "Shared Threat Actor", "type": "actor"}
    ]
    
    links = [
        {"source": "n1", "target": "n3", "relationship": "attributed_to", "weight": 0.9},
        {"source": "n2", "target": "n3", "relationship": "used_by", "weight": 0.8}
    ]
    
    return {
        "confidence_score": confidence,
        "nodes": nodes,
        "links": links,
        "status": "Correlated"
    }
