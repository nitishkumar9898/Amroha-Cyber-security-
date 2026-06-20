from typing import Dict, Any

def extract_lessons(incident_id: str, report_text: str) -> Dict[str, Any]:
    """
    Simulates automated extraction of lessons learned from an incident report.
    """
    knowledge = f"Threat actor utilized novel obfuscation in {incident_id}. Recommend patching edge nodes."
    
    return {
        "extracted_knowledge": knowledge,
        "relevance_score": 0.88,
        "status": "Extracted"
    }

def update_knowledge_graph(lesson_id: int, knowledge: str) -> Dict[str, Any]:
    """
    Simulates updating the organizational knowledge graph.
    """
    return {
        "lesson_id": lesson_id,
        "nodes_added": 2,
        "edges_added": 3,
        "status": "Graph Updated"
    }
