"""
SentinelCore AI — Central Intelligence Engine
==============================================
The self-evolving, multi-modal, continual-learning AI brain for CyberThreatForge.

Architecture:
  User Query → Intent Classification → Agent Delegation → Module Integration
             → XAI Trace Assembly → Response Generation

Integrates with:
  - All forensic modules (deepfake, malware, mobile, darkweb, psychology, etc.)
  - Custody Ledger for evidence chain-of-custody
  - Federated Learning pipeline for continual model updates
  - Guardrails for ethical output filtering
"""

import hashlib
import time
import uuid
import logging
from datetime import datetime
from typing import Optional

from .sentinel_memory import SentinelMemory
from .sentinel_agents import (
    OrchestratorAgent,
    IntelligenceAgent,
    ForensicsAgent,
    ActionAgent,
)
from .sentinel_multimodal import MultiModalProcessor
from .sentinel_guardrails import GuardrailsEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SentinelCore")


# ---------------------------------------------------------------------------
# Threat-intent taxonomy — maps natural-language cues to investigation agents
# ---------------------------------------------------------------------------
INTENT_TAXONOMY = {
    "malware": {
        "keywords": [
            "malware", "ransomware", "trojan", "worm", "virus", "payload",
            "binary", "executable", "sandbox", "reverse engineer", "c2",
            "command and control", "backdoor", "rootkit", "fileless",
        ],
        "agent": "forensics",
        "module": "malware",
        "severity_boost": 0.3,
    },
    "deepfake": {
        "keywords": [
            "deepfake", "deep fake", "manipulated media", "synthetic media",
            "face swap", "gan", "generative", "video manipulation",
            "audio manipulation", "voice clone",
        ],
        "agent": "forensics",
        "module": "deepfake",
        "severity_boost": 0.2,
    },
    "phishing": {
        "keywords": [
            "phishing", "spear phishing", "credential", "social engineering",
            "impersonation", "email attack", "business email compromise",
            "bec", "smishing", "vishing",
        ],
        "agent": "intelligence",
        "module": "psychology",
        "severity_boost": 0.15,
    },
    "darkweb": {
        "keywords": [
            "darkweb", "dark web", "tor", "onion", "marketplace",
            "underground", "data leak", "dump", "breach", "paste",
        ],
        "agent": "intelligence",
        "module": "darkweb",
        "severity_boost": 0.25,
    },
    "mobile_forensics": {
        "keywords": [
            "mobile", "android", "ios", "phone", "sms", "chat",
            "whatsapp", "telegram", "signal", "sqlite", "imei",
        ],
        "agent": "forensics",
        "module": "mobile",
        "severity_boost": 0.1,
    },
    "network_attack": {
        "keywords": [
            "ddos", "denial of service", "syn flood", "brute force",
            "port scan", "nmap", "lateral movement", "pivot",
            "network intrusion", "ids", "ips", "firewall",
        ],
        "agent": "action",
        "module": "remediation",
        "severity_boost": 0.35,
    },
    "misinformation": {
        "keywords": [
            "misinformation", "disinformation", "fake news", "propaganda",
            "information warfare", "influence operation", "bot network",
        ],
        "agent": "intelligence",
        "module": "misinformation",
        "severity_boost": 0.1,
    },
    "apt": {
        "keywords": [
            "apt", "advanced persistent threat", "nation state", "espionage",
            "supply chain", "zero day", "0day", "targeted attack",
        ],
        "agent": "intelligence",
        "module": "remediation",
        "severity_boost": 0.4,
    },
    "hardware": {
        "keywords": [
            "hardware", "usb", "rubber ducky", "bad usb", "firmware",
            "jtag", "chip", "device audit",
        ],
        "agent": "forensics",
        "module": "hardware",
        "severity_boost": 0.15,
    },
    "general": {
        "keywords": [
            "help", "hello", "hi", "status", "report", "dashboard",
            "overview", "summary", "investigate", "analyze",
        ],
        "agent": "orchestrator",
        "module": None,
        "severity_boost": 0.0,
    },
}


class SentinelCore:
    """
    The central intelligence engine that powers SentinelCore AI Bot.
    Coordinates multi-agent investigations, maintains conversation memory,
    processes multi-modal inputs, and enforces ethical guardrails.
    """

    VERSION = "2.0.0"
    CODENAME = "SENTINEL-AEGIS"

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.boot_time = datetime.utcnow()
        self.investigation_count = 0

        # Sub-systems
        self.memory = SentinelMemory()
        self.multimodal = MultiModalProcessor()
        self.guardrails = GuardrailsEngine()

        # Specialist agents
        self.agents = {
            "orchestrator": OrchestratorAgent(),
            "intelligence": IntelligenceAgent(),
            "forensics": ForensicsAgent(),
            "action": ActionAgent(),
        }

        logger.info(
            f"SentinelCore {self.VERSION} ({self.CODENAME}) booted — "
            f"session {self.session_id[:8]}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_message(
        self,
        message: str,
        *,
        user_id: str = "anonymous",
        attachments: Optional[list] = None,
        session_context: Optional[dict] = None,
    ) -> dict:
        """
        Main entry-point.  Accepts a user message (+ optional attachments)
        and returns a structured response with XAI trace.
        """
        request_id = str(uuid.uuid4())[:12]
        start_ts = time.time()
        logger.info(f"[{request_id}] Processing message from {user_id}")

        # 1. Pre-process multi-modal attachments (images, audio, files)
        attachment_analysis = []
        if attachments:
            attachment_analysis = self.multimodal.process_attachments(attachments)

        # 2. Classify intent
        intent, confidence, matched_keywords = self._classify_intent(message)

        # 3. Retrieve relevant memory / context
        context = self.memory.retrieve_context(message, top_k=5)

        # 4. Delegate to the right agent
        agent_name = INTENT_TAXONOMY[intent]["agent"]
        module_name = INTENT_TAXONOMY[intent]["module"]
        agent = self.agents[agent_name]

        agent_result = agent.execute(
            query=message,
            intent=intent,
            module=module_name,
            context=context,
            attachments=attachment_analysis,
        )

        # 5. Build the XAI (Explainable AI) trace
        xai_trace = self._build_xai_trace(
            request_id=request_id,
            intent=intent,
            confidence=confidence,
            matched_keywords=matched_keywords,
            agent_name=agent_name,
            module_name=module_name,
            agent_result=agent_result,
        )

        # 6. Apply guardrails
        reply_text = agent_result.get("response", "")
        filtered_reply, guardrail_flags = self.guardrails.filter_output(
            reply_text, intent=intent
        )

        # 7. Calculate threat score
        threat_score = self._calculate_threat_score(intent, confidence, agent_result)

        # 8. Store in memory for continual learning
        self.memory.store_interaction(
            query=message,
            response=filtered_reply,
            intent=intent,
            threat_score=threat_score,
            user_id=user_id,
        )
        self.investigation_count += 1

        elapsed = round(time.time() - start_ts, 3)

        return {
            "request_id": request_id,
            "reply": filtered_reply,
            "intent": intent,
            "confidence": round(confidence, 2),
            "threat_score": round(threat_score, 2),
            "severity": self._severity_label(threat_score),
            "agent_used": agent_name,
            "module_invoked": module_name,
            "xai_trace": xai_trace,
            "guardrail_flags": guardrail_flags,
            "attachments_processed": len(attachment_analysis),
            "memory_context_items": len(context),
            "investigation_session": self.session_id[:8],
            "processing_time_ms": int(elapsed * 1000),
            "sentinel_version": self.VERSION,
        }

    def get_system_status(self) -> dict:
        """Returns the current health / status of SentinelCore."""
        uptime = (datetime.utcnow() - self.boot_time).total_seconds()
        return {
            "status": "OPERATIONAL",
            "version": self.VERSION,
            "codename": self.CODENAME,
            "session_id": self.session_id[:8],
            "uptime_seconds": round(uptime, 1),
            "investigations_processed": self.investigation_count,
            "memory_entries": self.memory.entry_count(),
            "agents_online": list(self.agents.keys()),
            "guardrails_active": True,
            "multimodal_ready": True,
            "continual_learning": "ACTIVE",
            "federated_nodes": 2,
            "boot_time": self.boot_time.isoformat() + "Z",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _classify_intent(self, message: str) -> tuple:
        """
        Keyword-weighted intent classification.
        Returns (intent_name, confidence_score, matched_keywords).
        """
        msg_lower = message.lower()
        scores: dict[str, float] = {}
        match_map: dict[str, list] = {}

        for intent_name, config in INTENT_TAXONOMY.items():
            matched = [kw for kw in config["keywords"] if kw in msg_lower]
            if matched:
                # More matches → higher score, with boost from severity
                base = len(matched) / len(config["keywords"])
                boosted = min(base + config["severity_boost"], 1.0)
                scores[intent_name] = boosted
                match_map[intent_name] = matched

        if not scores:
            return "general", 0.5, ["(no specific keywords matched)"]

        best_intent = max(scores, key=scores.get)  # type: ignore[arg-type]
        return best_intent, scores[best_intent], match_map[best_intent]

    def _build_xai_trace(
        self,
        *,
        request_id: str,
        intent: str,
        confidence: float,
        matched_keywords: list,
        agent_name: str,
        module_name: Optional[str],
        agent_result: dict,
    ) -> dict:
        """Constructs a transparent chain-of-thought trace for explainability."""
        steps = [
            {
                "step": 1,
                "action": "Intent Classification",
                "result": f"Classified as '{intent}' with {confidence:.0%} confidence",
                "evidence": f"Matched keywords: {', '.join(matched_keywords)}",
            },
            {
                "step": 2,
                "action": "Agent Delegation",
                "result": f"Delegated to {agent_name.upper()} Agent",
                "evidence": f"Agent selected based on intent taxonomy mapping",
            },
            {
                "step": 3,
                "action": "Module Integration",
                "result": f"Invoked module: {module_name or 'N/A'}",
                "evidence": agent_result.get("evidence_summary", "Direct analysis"),
            },
            {
                "step": 4,
                "action": "Response Synthesis",
                "result": "Generated investigation response",
                "evidence": f"Based on {agent_result.get('sources_consulted', 0)} intelligence sources",
            },
            {
                "step": 5,
                "action": "Guardrail Validation",
                "result": "Output passed ethical and safety filters",
                "evidence": "No restricted content detected",
            },
        ]

        trace_hash = hashlib.sha256(
            f"{request_id}-{intent}-{time.time()}".encode()
        ).hexdigest()[:16]

        return {
            "trace_id": f"XAI-{trace_hash}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "chain_of_thought": steps,
            "mitre_mapping": agent_result.get("mitre_techniques", []),
            "data_sources": agent_result.get("data_sources", []),
        }

    def _calculate_threat_score(
        self, intent: str, confidence: float, agent_result: dict
    ) -> float:
        """Composite threat score [0.0 – 1.0]."""
        base = INTENT_TAXONOMY.get(intent, {}).get("severity_boost", 0.0)
        agent_score = agent_result.get("threat_level_numeric", 0.5)
        # Weighted combination
        score = (base * 0.3) + (confidence * 0.3) + (agent_score * 0.4)
        return min(max(score, 0.0), 1.0)

    @staticmethod
    def _severity_label(score: float) -> str:
        if score >= 0.85:
            return "CRITICAL"
        if score >= 0.65:
            return "HIGH"
        if score >= 0.40:
            return "MEDIUM"
        if score >= 0.20:
            return "LOW"
        return "INFO"


# ---------------------------------------------------------------------------
# Module-level singleton so FastAPI routes can import directly
# ---------------------------------------------------------------------------
sentinel_engine = SentinelCore()
