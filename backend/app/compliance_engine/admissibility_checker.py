# compliance_engine/admissibility_checker.py
"""Legal admissibility checker for digital evidence.
Implements basic checks based on Indian IT Act 2000 and DPDP Act 2023.
In production replace with a comprehensive rule base.
"""
from typing import Dict, Any


def check_it_act_2000(evidence: Dict[str, Any]) -> bool:
    """Placeholder check for IT Act 2000 Section 5 compliance.
    Returns True if evidence collection method is recognized as forensic tool.
    """
    method = evidence.get("collection_method")
    return method == "forensic_tool"


def check_dpdp_2023(evidence: Dict[str, Any]) -> bool:
    """Placeholder check for DPDP Act 2023 consent requirements.
    Returns True if personal data has explicit consent flag.
    """
    return bool(evidence.get("has_consent"))


def is_admissible(evidence: Dict[str, Any]) -> bool:
    """Overall admissibility decision combining multiple legal checks.
    """
    return check_it_act_2000(evidence) and check_dpdp_2023(evidence)
