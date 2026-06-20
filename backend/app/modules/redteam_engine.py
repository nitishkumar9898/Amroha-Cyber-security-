import random
import uuid
from typing import Dict, Any, List

class AgenticScenarioGenerator:
    """Mock agentic AI generator for creating abstract scenarios."""
    
    @staticmethod
    def generate(name: str) -> Dict[str, Any]:
        """Generates a mock abstract attack graph."""
        nodes = [
            {"id": "entry", "type": "phishing", "success_prob": 0.3},
            {"id": "privesc", "type": "local_exploit", "success_prob": 0.5},
            {"id": "lateral", "type": "pass_the_hash", "success_prob": 0.4},
            {"id": "target", "type": "data_exfil", "success_prob": 0.8}
        ]
        
        edges = [
            {"from": "entry", "to": "privesc"},
            {"from": "privesc", "to": "lateral"},
            {"from": "lateral", "to": "target"}
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "complexity": random.choice(["Low", "Medium", "High"])
        }

class BlueVsRedSimulator:
    """Mock state machine simulator for Blue vs Red team exercises."""
    
    def __init__(self, scenario_graph: Dict[str, Any]):
        self.graph = scenario_graph
        self.state = "active"
        self.current_node_index = 0
        self.red_progress = 0
        self.blue_defenses_deployed = 0
    
    def apply_action(self, team: str, action_type: str, target: str) -> Dict[str, Any]:
        """Apply an action to the simulation state."""
        if self.state != "active":
            return {"status": "error", "message": "Simulation not active."}
            
        result = {}
        if team == 'red':
            # Mock red team progress
            if random.random() > 0.3: # 70% success rate on actions unless blocked
                self.red_progress += 1
                result = {"action": "success", "message": f"Red team successfully executed {action_type} on {target}."}
            else:
                result = {"action": "failed", "message": f"Red team failed to execute {action_type} on {target}."}
                
        elif team == 'blue':
            # Mock blue team defense
            self.blue_defenses_deployed += 1
            result = {"action": "success", "message": f"Blue team deployed {action_type} on {target}."}
            
        # Check end conditions (mock logic)
        if self.red_progress >= len(self.graph.get("nodes", [])):
            self.state = "red_win"
        elif self.blue_defenses_deployed > 3:
            self.state = "blue_win"
            
        return result

class PostExerciseAnalyzer:
    """Generates recommendations based on simulation metrics."""
    
    @staticmethod
    def analyze(metrics: Dict[str, Any]) -> List[str]:
        recommendations = []
        if metrics.get("red_progress", 0) > 2:
            recommendations.append("High risk of lateral movement. Implement stricter network segmentation.")
        if metrics.get("blue_defenses_deployed", 0) < 2:
            recommendations.append("Blue team response time is lacking. Automate initial containment protocols.")
            
        if not recommendations:
            recommendations.append("Good defensive posture observed. Continue regular training exercises.")
            
        return recommendations
