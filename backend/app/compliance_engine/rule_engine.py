# compliance_engine/rule_engine.py
"""Simple rule engine for legal compliance.
Provides a DSL to define and evaluate compliance rules.
Currently a thin wrapper around Python callables for extensibility.
"""

from typing import Callable, List, Dict, Any

class ComplianceRule:
    def __init__(self, name: str, description: str, condition: Callable[[Dict[str, Any]], bool]):
        self.name = name
        self.description = description
        self.condition = condition

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the rule against the provided context."""
        try:
            return self.condition(context)
        except Exception as e:
            # In production, log the error
            return False

class RuleEngine:
    def __init__(self):
        self.rules: List[ComplianceRule] = []

    def add_rule(self, rule: ComplianceRule):
        self.rules.append(rule)

    def evaluate_all(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """Return a mapping of rule name to evaluation result."""
        return {rule.name: rule.evaluate(context) for rule in self.rules}

# Example usage (to be removed or placed in tests)
if __name__ == "__main__":
    engine = RuleEngine()
    engine.add_rule(ComplianceRule(
        name="ITAct2000_Section5",
        description="Check if evidence collection method complies with Section 5 of IT Act 2000",
        condition=lambda ctx: ctx.get('method') == 'forensic_tool'
    ))
    print(engine.evaluate_all({'method': 'forensic_tool'}))
