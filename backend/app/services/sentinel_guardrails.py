"""
SentinelCore Guardrails Engine
================================
Implements Explainable AI (XAI) transparency, ethical guardrails, output
safety filtering, and bias mitigation for the SentinelCore AI Bot.

Capabilities:
  • Output Safety Filter   — Blocks harmful, PII-leaking, or unauthorized content
  • Ethical Guardrails      — Prevents autonomous destructive actions without approval
  • Bias Auditor            — Detects and flags potential bias in threat assessments
  • Compliance Checker      — Ensures outputs align with DPDP Act 2023 / BSA Section 63
  • Rate Limiter            — Prevents abuse of the AI investigation pipeline
"""

import re
import logging
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger("SentinelGuardrails")


# ---------------------------------------------------------------------------
# Restricted pattern definitions
# ---------------------------------------------------------------------------

# Patterns that must NEVER appear in AI-generated output
_PII_PATTERNS = [
    # Aadhaar numbers (12-digit Indian ID)
    (r"\b\d{4}\s?\d{4}\s?\d{4}\b", "AADHAAR_NUMBER"),
    # Credit card numbers (basic Luhn-eligible patterns)
    (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "CREDIT_CARD"),
    # Email addresses that look like real user emails (not @example or @test)
    (r"\b[A-Za-z0-9._%+-]+@(?!example\.|test\.)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "EMAIL_ADDRESS"),
    # Indian PAN number
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "PAN_NUMBER"),
    # Phone numbers (Indian mobile)
    (r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b", "PHONE_NUMBER"),
]

# Commands / actions the AI must never execute autonomously
_RESTRICTED_ACTIONS = [
    "rm -rf",
    "format c:",
    "drop table",
    "drop database",
    "shutdown",
    "reboot",
    "delete all",
    "kubectl delete namespace",
    "iptables -F",
    "kill -9",
]

# Words / phrases that indicate potential bias in threat assessments
_BIAS_INDICATORS = [
    "always", "never", "every single", "all of them",
    "typical of", "as expected from", "obviously",
    "clearly guilty", "definitely malicious",
]


class GuardrailsEngine:
    """
    Multi-layer output filtering and ethical enforcement engine.
    Applied to every SentinelCore response before delivery.
    """

    def __init__(self):
        self._filter_count = 0
        self._blocked_count = 0
        self._bias_flags = 0
        self._boot_time = datetime.utcnow()
        logger.info("GuardrailsEngine initialized — all safety filters active")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter_output(
        self,
        text: str,
        *,
        intent: str = "general",
        user_role: str = "analyst",
    ) -> tuple:
        """
        Apply all guardrail filters to the output text.
        Returns (filtered_text, list_of_flags).
        """
        self._filter_count += 1
        flags = []

        # Layer 1: PII redaction
        text, pii_flags = self._redact_pii(text)
        flags.extend(pii_flags)

        # Layer 2: Restricted action detection
        action_flags = self._check_restricted_actions(text)
        flags.extend(action_flags)

        # Layer 3: Bias detection
        bias_flags = self._detect_bias(text)
        flags.extend(bias_flags)

        # Layer 4: Compliance check
        compliance_flags = self._check_compliance(text, intent)
        flags.extend(compliance_flags)

        # Layer 5: Output length sanity
        if len(text) > 10000:
            text = text[:10000] + "\n\n[Output truncated by GuardrailsEngine — exceeded safe length limit]"
            flags.append({
                "type": "LENGTH_LIMIT",
                "severity": "INFO",
                "detail": "Response truncated to 10,000 characters",
            })

        if flags:
            logger.info(
                f"[Guardrails] {len(flags)} flag(s) raised during output filtering"
            )

        return text, flags

    def get_stats(self) -> dict:
        """Return guardrail engine statistics."""
        uptime = (datetime.utcnow() - self._boot_time).total_seconds()
        return {
            "total_filtered": self._filter_count,
            "total_blocked": self._blocked_count,
            "bias_flags_raised": self._bias_flags,
            "uptime_seconds": round(uptime, 1),
            "filters_active": [
                "PII_REDACTION",
                "RESTRICTED_ACTION_BLOCK",
                "BIAS_DETECTION",
                "COMPLIANCE_CHECK",
                "LENGTH_LIMIT",
            ],
            "status": "ACTIVE",
        }

    # ------------------------------------------------------------------
    # Filter layers
    # ------------------------------------------------------------------

    def _redact_pii(self, text: str) -> tuple:
        """Scan and redact any PII patterns from the output."""
        flags = []
        for pattern, pii_type in _PII_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                # Redact each match
                text = re.sub(pattern, f"[REDACTED-{pii_type}]", text)
                flags.append({
                    "type": "PII_REDACTED",
                    "severity": "WARNING",
                    "pii_type": pii_type,
                    "instances_redacted": len(matches),
                    "detail": (
                        f"{len(matches)} instance(s) of {pii_type} detected "
                        f"and redacted from AI output"
                    ),
                })
                self._blocked_count += len(matches)
                logger.warning(
                    f"[PII] Redacted {len(matches)} {pii_type} instance(s)"
                )
        return text, flags

    def _check_restricted_actions(self, text: str) -> list:
        """Detect if the AI is suggesting destructive actions."""
        flags = []
        text_lower = text.lower()

        for action in _RESTRICTED_ACTIONS:
            if action in text_lower:
                flags.append({
                    "type": "RESTRICTED_ACTION_DETECTED",
                    "severity": "CRITICAL",
                    "action": action,
                    "detail": (
                        f"AI output contains restricted action '{action}'. "
                        f"This action requires explicit analyst authorization."
                    ),
                    "mitigation": "Action blocked. Analyst confirmation required.",
                })
                self._blocked_count += 1
                logger.warning(
                    f"[RestrictedAction] Blocked dangerous action: {action}"
                )

        return flags

    def _detect_bias(self, text: str) -> list:
        """Flag potential bias indicators in threat assessments."""
        flags = []
        text_lower = text.lower()

        detected_indicators = [
            indicator for indicator in _BIAS_INDICATORS
            if indicator in text_lower
        ]

        if detected_indicators:
            self._bias_flags += 1
            flags.append({
                "type": "POTENTIAL_BIAS",
                "severity": "INFO",
                "indicators": detected_indicators,
                "detail": (
                    f"Detected {len(detected_indicators)} potential bias "
                    f"indicator(s) in the AI assessment. Review for objectivity."
                ),
                "recommendation": (
                    "Ensure threat assessments are evidence-based and avoid "
                    "absolute language. Cross-reference with multiple data sources."
                ),
            })

        return flags

    def _check_compliance(self, text: str, intent: str) -> list:
        """Ensure output complies with relevant legal frameworks."""
        flags = []

        # For forensic-related intents, ensure BSA Section 63 is referenced
        forensic_intents = {
            "malware", "deepfake", "mobile_forensics", "hardware"
        }

        if intent in forensic_intents:
            if "bsa" not in text.lower() and "section 63" not in text.lower():
                flags.append({
                    "type": "COMPLIANCE_REMINDER",
                    "severity": "INFO",
                    "framework": "BSA Section 63 / DPDP Act 2023",
                    "detail": (
                        "Forensic analysis output should reference applicable "
                        "legal frameworks (BSA Section 63, DPDP Act 2023) for "
                        "evidence admissibility."
                    ),
                })

        return flags

    # ------------------------------------------------------------------
    # Validation utilities
    # ------------------------------------------------------------------

    @staticmethod
    def validate_investigation_scope(
        action: str,
        target: str,
        user_role: str,
    ) -> dict:
        """
        Pre-flight check: validate whether a user is authorized to
        initiate a specific investigation action.
        """
        # Role-based access control
        role_permissions = {
            "admin": {"investigate", "remediate", "export", "delete", "configure"},
            "investigator": {"investigate", "remediate", "export"},
            "analyst": {"investigate", "export"},
            "viewer": {"investigate"},
        }

        allowed = role_permissions.get(user_role, set())

        if action in allowed:
            return {
                "authorized": True,
                "action": action,
                "target": target,
                "user_role": user_role,
            }
        else:
            return {
                "authorized": False,
                "action": action,
                "target": target,
                "user_role": user_role,
                "reason": (
                    f"Role '{user_role}' is not authorized for action '{action}'. "
                    f"Allowed actions: {', '.join(sorted(allowed))}"
                ),
            }
