# backend/app/services/gse_adapter.py
"""GSE (Generative Simulation Engine) adapter.
Integrates the training simulator with the RedTeamForge Agentic AI generator
to dynamically spin up customized training scenarios.
"""

from typing import Dict
from ..modules.redteam_engine import AgenticScenarioGenerator

def get_scenario_for_user(user_id: str) -> Dict:
    """Return an agentically generated scenario configuration.
    Args:
        user_id: Identifier of the trainee.
    Returns:
        A dict representing scenario metadata that can be stored in the TrainingSession.config column.
    """
    # Use the RedTeamForge Agentic Generator
    scenario_graph = AgenticScenarioGenerator.generate(f"Training for {user_id}")
    
    # Map the abstract nodes to GSE display labels
    nodes = []
    for idx, node in enumerate(scenario_graph.get("nodes", [])):
        nodes.append({
            "id": node.get("id", idx),
            "type": node.get("type", "unknown"),
            "label": f"Node {node.get('id', idx)}"
        })
    
    return {
        "scenario_id": f"gen-{user_id}-001",
        "description": "Agentically generated red team attack scenario.",
        "nodes": nodes,
        "edges": scenario_graph.get("edges", []),
        "complexity": scenario_graph.get("complexity", "Medium"),
        "hints": [
            "Monitor anomalous network traffic.",
            "Verify endpoint processes and check for lateral movement."
        ],
    }
}
