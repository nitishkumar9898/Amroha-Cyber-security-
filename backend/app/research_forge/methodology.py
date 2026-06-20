# research_forge/methodology.py
"""Research methodology framework implementation.
Provides classes to define research objectives, hypotheses, design, and
step‑by‑step execution plan.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Objective:
    """A single research objective."""
    description: str
    metrics: List[str] = field(default_factory=list)

@dataclass
class Hypothesis:
    """A hypothesis linking variables."""
    statement: str
    tested: bool = False
    result: Any = None

@dataclass
class ResearchDesign:
    """Container for the overall research design."""
    objectives: List[Objective] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    methodology: str = ""  # e.g., "Experimental", "Observational"
    resources: Dict[str, Any] = field(default_factory=dict)

    def add_objective(self, description: str, metrics: List[str] = None):
        metrics = metrics or []
        self.objectives.append(Objective(description, metrics))

    def add_hypothesis(self, statement: str):
        self.hypotheses.append(Hypothesis(statement))

    def to_dict(self) -> dict:
        """Serialise the design for storage or reporting."""
        return {
            "objectives": [vars(o) for o in self.objectives],
            "hypotheses": [vars(h) for h in self.hypotheses],
            "methodology": self.methodology,
            "resources": self.resources,
        }
