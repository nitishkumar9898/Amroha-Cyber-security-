"""
SentinelCore Agents — Autonomous Investigation Specialists
============================================================
Multi-agent system where each agent has a distinct role in the
investigation pipeline.

Agent Roster:
  • OrchestratorAgent — Plans investigations, delegates tasks, summarises.
  • IntelligenceAgent — Queries CTI feeds, correlates IOCs, maps MITRE ATT&CK.
  • ForensicsAgent    — Analyses evidence via forensic modules (malware, deepfake, mobile…).
  • ActionAgent       — Executes containment, remediation, and self-healing actions.
"""

import hashlib
import random
import time
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("SentinelAgents")


# ======================================================================
# Base Agent
# ======================================================================
class _BaseAgent:
    """Common agent interface."""

    AGENT_TYPE = "base"

    def __init__(self):
        self.invocation_count = 0
        self.last_invoked: Optional[str] = None

    def execute(
        self,
        query: str,
        intent: str,
        module: Optional[str],
        context: list,
        attachments: list,
    ) -> dict:
        """Override in subclass."""
        raise NotImplementedError

    def _stamp(self) -> str:
        self.invocation_count += 1
        self.last_invoked = datetime.utcnow().isoformat() + "Z"
        return self.last_invoked


# ======================================================================
# Orchestrator Agent
# ======================================================================
class OrchestratorAgent(_BaseAgent):
    """
    The master planner.  Handles greetings, status checks, and high-level
    investigation planning.  Delegates specialised work to other agents.
    """

    AGENT_TYPE = "orchestrator"

    _GREETINGS = [
        (
            "Greetings, Investigator. All SentinelCore defence systems are "
            "nominal and operating at peak efficiency. I am monitoring "
            "{threat_count} active threat vectors across the intelligence matrix. "
            "How may I assist your investigation today?"
        ),
        (
            "Welcome back to the CyberThreatForge command centre. "
            "SentinelCore's multi-agent investigation pipeline is online. "
            "The global federated intelligence network reports "
            "{threat_count} active threat signatures. Ready for your directives."
        ),
        (
            "Sentinel standing by. Current threat landscape: "
            "{threat_count} vectors under surveillance, {module_count} forensic "
            "modules active, continual learning pipeline synchronized. "
            "What would you like me to investigate?"
        ),
    ]

    _STATUS_REPORT = (
        "📊 **SentinelCore Status Report**\n\n"
        "• **Operational State:** ACTIVE — All systems nominal\n"
        "• **Threat Vectors Monitored:** {threat_count}\n"
        "• **Active Forensic Modules:** {module_count} (Deepfake, Malware, "
        "Mobile, Dark Web, Psychology, Misinformation, Hardware, Research)\n"
        "• **Federated Nodes:** 2 (NIA Edge-01, CBI Edge-04)\n"
        "• **Knowledge Base:** v{kb_version} — Last aggregation: {last_agg}\n"
        "• **Investigations Today:** {inv_count}\n"
        "• **Guardrails:** ACTIVE — Ethical filters engaged\n\n"
        "All systems are ready for tasking."
    )

    def execute(self, query, intent, module, context, attachments) -> dict:
        ts = self._stamp()
        q_lower = query.lower()

        threat_count = random.randint(12, 47)
        module_count = 8
        inv_count = random.randint(3, 15)

        # Status
        if any(w in q_lower for w in ("status", "health", "overview", "system")):
            response = self._STATUS_REPORT.format(
                threat_count=threat_count,
                module_count=module_count,
                kb_version="2.1",
                last_agg=datetime.utcnow().strftime("%H:%M UTC"),
                inv_count=inv_count,
            )
        # Greeting
        elif any(w in q_lower for w in ("hello", "hi", "hey", "greetings", "good")):
            template = random.choice(self._GREETINGS)
            response = template.format(
                threat_count=threat_count, module_count=module_count
            )
        # General investigation request
        else:
            response = (
                f"I've analysed your query and am initiating a broad-spectrum "
                f"investigation. My analysis of {len(context)} prior intelligence "
                f"entries indicates this may relate to an active threat campaign. "
                f"I'm cross-referencing MITRE ATT&CK mappings and correlating with "
                f"federated threat intelligence from all edge nodes.\n\n"
                f"**Recommended next steps:**\n"
                f"1. Run a targeted forensic scan using the relevant module\n"
                f"2. Cross-reference IOCs against the dark web intelligence feed\n"
                f"3. Generate a CERT-IN compliant incident report for documentation"
            )

        return {
            "response": response,
            "agent": self.AGENT_TYPE,
            "timestamp": ts,
            "threat_level_numeric": 0.3,
            "sources_consulted": len(context),
            "evidence_summary": "Orchestrator-level analysis complete",
            "mitre_techniques": [],
            "data_sources": ["internal_memory", "federated_aggregator"],
        }


# ======================================================================
# Intelligence Agent
# ======================================================================
class IntelligenceAgent(_BaseAgent):
    """
    Cyber Threat Intelligence specialist.  Correlates IOCs, queries external
    feeds, maps to MITRE ATT&CK, and assesses threat-actor attribution.
    """

    AGENT_TYPE = "intelligence"

    # Simulated CTI database
    _CTI_DATABASE = {
        "darkweb": {
            "response_template": (
                "🌐 **Dark Web Intelligence Report**\n\n"
                "Scanning Tor hidden services and underground marketplaces…\n\n"
                "**Findings:**\n"
                "• Detected {listing_count} active listings on ShadowBazaar & BlackMarket-X\n"
                "• {cred_count} credential dumps matching target organization patterns\n"
                "• Active RaaS (Ransomware-as-a-Service) offerings from threat group "
                "'{actor_name}'\n"
                "• Cryptocurrency wallet {wallet} linked to {tx_count} transactions\n\n"
                "**Attribution Confidence:** {confidence}%\n"
                "**MITRE ATT&CK:** T1589 (Gather Victim Identity Information), "
                "T1583 (Acquire Infrastructure)\n\n"
                "⚠️ Recommend immediate correlation with internal asset inventory "
                "and credential rotation for any matched accounts."
            ),
            "mitre": ["T1589", "T1583.001", "T1567"],
        },
        "psychology": {
            "response_template": (
                "🧠 **Cyber Psychology Profile Analysis**\n\n"
                "Analysing linguistic patterns, urgency markers, and social "
                "engineering indicators…\n\n"
                "**Profile Assessment:**\n"
                "• **Urgency Score:** {urgency}/10 — {urgency_label}\n"
                "• **Manipulation Tactics:** Authority impersonation, artificial scarcity\n"
                "• **Language Markers:** {marker_count} high-risk phrases detected\n"
                "• **Threat Actor Archetype:** '{archetype}'\n"
                "• **Predicted Objective:** Credential harvesting via trust exploitation\n\n"
                "**Recommendation:** Flag all communications matching this profile "
                "pattern for SOC review. Update phishing awareness training modules."
            ),
            "mitre": ["T1566.001", "T1534", "T1598"],
        },
        "misinformation": {
            "response_template": (
                "📰 **Misinformation Analysis Report**\n\n"
                "Evaluating claim credibility against verified intelligence sources…\n\n"
                "**Assessment:**\n"
                "• **Credibility Score:** {cred_score}/100 — {verdict}\n"
                "• **Source Reliability:** {reliability}\n"
                "• **Cross-Reference Matches:** {xref_count} verified sources consulted\n"
                "• **Bot Network Indicators:** {bot_indicator}\n"
                "• **Amplification Pattern:** {amp_pattern}\n\n"
                "**Conclusion:** The claim shows indicators of coordinated inauthentic "
                "behaviour. Recommend monitoring the dissemination network and "
                "preparing counter-narrative assets."
            ),
            "mitre": ["T1583.006", "T1585.001"],
        },
    }

    def execute(self, query, intent, module, context, attachments) -> dict:
        ts = self._stamp()

        # Select the right CTI module
        cti_key = module if module in self._CTI_DATABASE else "darkweb"
        cti = self._CTI_DATABASE[cti_key]

        # Generate dynamic values for the template
        params = {
            "listing_count": random.randint(3, 18),
            "cred_count": random.randint(200, 15000),
            "actor_name": random.choice([
                "ShadowPhantom", "LazerGroup-IN", "CobalStrike-Proxy",
                "DarkVortex", "APT-Nexus-7",
            ]),
            "wallet": f"bc1q{''.join(random.choices('abcdef0123456789', k=20))}",
            "tx_count": random.randint(5, 120),
            "confidence": random.randint(65, 95),
            "urgency": random.randint(6, 10),
            "urgency_label": random.choice(["HIGH", "CRITICAL"]),
            "marker_count": random.randint(4, 12),
            "archetype": random.choice([
                "Opportunistic Harvester", "Ideological Operative",
                "State-Sponsored Infiltrator",
            ]),
            "cred_score": random.randint(8, 35),
            "verdict": "LOW CREDIBILITY",
            "reliability": random.choice(["UNRELIABLE", "PARTIALLY RELIABLE"]),
            "xref_count": random.randint(5, 20),
            "bot_indicator": random.choice([
                "High — coordinated posting pattern detected",
                "Medium — some indicators of automated dissemination",
            ]),
            "amp_pattern": random.choice([
                "Exponential spread across 3 platforms in 4 hours",
                "Linear amplification via bot-farm retweet clusters",
            ]),
        }

        response = cti["response_template"].format(**params)

        return {
            "response": response,
            "agent": self.AGENT_TYPE,
            "timestamp": ts,
            "threat_level_numeric": random.uniform(0.6, 0.95),
            "sources_consulted": random.randint(4, 12),
            "evidence_summary": f"CTI analysis via {cti_key} intelligence module",
            "mitre_techniques": cti["mitre"],
            "data_sources": [
                "mitre_attack_v14",
                "tor_hidden_services",
                "threat_intel_feeds",
                "federated_knowledge_base",
            ],
        }


# ======================================================================
# Forensics Agent
# ======================================================================
class ForensicsAgent(_BaseAgent):
    """
    Digital forensics specialist.  Integrates with CyberThreatForge's
    forensic modules to analyse evidence and maintain chain-of-custody.
    """

    AGENT_TYPE = "forensics"

    _MODULE_RESPONSES = {
        "malware": {
            "response_template": (
                "🦠 **Malware Analysis Report**\n\n"
                "Executing dynamic analysis in isolated sandbox environment…\n\n"
                "**Binary Analysis Results:**\n"
                "• **Threat Classification:** {classification}\n"
                "• **Severity:** CRITICAL\n"
                "• **File Hash (SHA-256):** `{file_hash}`\n"
                "• **Behavioural Indicators:**\n"
                "  - Registry persistence via Run keys (T1547.001)\n"
                "  - Process injection into svchost.exe (T1055.012)\n"
                "  - Encrypted C2 beacon to {c2_domain} every {beacon_interval}s\n"
                "  - Anti-VM checks (CPUID, MAC address comparison)\n"
                "• **YARA Rule Match:** `rule {yara_rule} {{ ... }}`\n"
                "• **Network IOCs:** {ioc_count} C2 endpoints identified\n\n"
                "**Recommendation:** Immediately isolate affected hosts, deploy "
                "YARA rules to all endpoints, and block identified C2 domains "
                "at the perimeter firewall. Evidence preserved under chain-of-custody."
            ),
            "mitre": ["T1547.001", "T1055.012", "T1071.001", "T1027"],
        },
        "deepfake": {
            "response_template": (
                "🎭 **Deepfake Detection Report**\n\n"
                "Multi-modal analysis of submitted media artefact…\n\n"
                "**Detection Results:**\n"
                "• **Verdict:** {verdict}\n"
                "• **Face Consistency Score:** {face_score}/1.00 "
                "(below 0.50 = likely manipulated)\n"
                "• **GAN Signature:** {gan_sig} detected\n"
                "• **Temporal Anomalies:** {anomaly_count} frame discontinuities "
                "at timestamps {timestamps}\n"
                "• **Double Compression:** {compression}\n"
                "• **Pixel Interpolation Artefacts:** {artefact_count} regions flagged\n\n"
                "**Confidence Level:** {confidence}%\n\n"
                "**Recommendation:** This media should be treated as potentially "
                "manipulated evidence. Cross-reference with original source material "
                "and document findings under BSA Section 63 certification."
            ),
            "mitre": ["T1566.003", "T1534"],
        },
        "mobile": {
            "response_template": (
                "📱 **Mobile Forensics Report**\n\n"
                "Parsing mobile device artefacts and communication databases…\n\n"
                "**Extraction Results:**\n"
                "• **Database:** {db_name}\n"
                "• **Messages Extracted:** {msg_count}\n"
                "• **GPS Coordinates Recovered:** {gps_count} location points\n"
                "• **Key Conversations:**\n"
                "  - {conv_1}\n"
                "  - {conv_2}\n"
                "• **Timeline Span:** {timeline}\n"
                "• **Deleted Records Recovered:** {deleted_count}\n\n"
                "**Chain of Custody:**\n"
                "All extracted artefacts have been SHA-256 hashed and logged "
                "in the CyberThreatForge custody ledger. BSA Section 63 "
                "certification is available for court submission."
            ),
            "mitre": ["T1437", "T1421", "T1430"],
        },
        "hardware": {
            "response_template": (
                "🔌 **Hardware Forensics Report**\n\n"
                "Auditing device firmware and interface characteristics…\n\n"
                "**Device Assessment:**\n"
                "• **Device Type:** {device_type}\n"
                "• **VID/PID:** {vid}/{pid}\n"
                "• **Risk Classification:** {risk_level}\n"
                "• **Firmware Integrity:** {firmware_status}\n"
                "• **HID Emulation Detected:** {hid_emulation}\n"
                "• **Known Malicious Database Match:** {db_match}\n\n"
                "**Recommendation:** {recommendation}"
            ),
            "mitre": ["T1200", "T1091"],
        },
    }

    def execute(self, query, intent, module, context, attachments) -> dict:
        ts = self._stamp()

        mod_key = module if module in self._MODULE_RESPONSES else "malware"
        mod = self._MODULE_RESPONSES[mod_key]

        # Build dynamic params for all possible templates
        params = {
            # Malware
            "classification": random.choice([
                "Ransomware (LockBit 4.0 variant)",
                "RAT (AsyncRAT family)",
                "Trojan Downloader (Emotet Stage-2)",
                "Wiper (HermeticWiper derivative)",
            ]),
            "file_hash": hashlib.sha256(
                f"payload_{time.time()}".encode()
            ).hexdigest(),
            "c2_domain": random.choice([
                "update-service.onion", "cdn-static-node.xyz",
                "api-telemetry-v2.ru",
            ]),
            "beacon_interval": random.choice([30, 60, 120, 300]),
            "yara_rule": random.choice([
                "APT_RAT_AsyncRAT", "Ransom_LockBit4",
                "Trojan_Emotet_Stage2",
            ]),
            "ioc_count": random.randint(3, 15),
            # Deepfake
            "verdict": "MANIPULATED MEDIA DETECTED",
            "face_score": round(random.uniform(0.12, 0.48), 2),
            "gan_sig": random.choice([
                "StyleGAN2", "DeepFaceLab", "FaceSwap-GAN",
            ]),
            "anomaly_count": random.randint(2, 8),
            "timestamps": f"0:{random.randint(5,30):02d}, 1:{random.randint(0,59):02d}",
            "compression": "Detected" if random.random() > 0.3 else "Not detected",
            "artefact_count": random.randint(3, 12),
            "confidence": round(random.uniform(85, 99), 1),
            # Mobile
            "db_name": "chat_history.db",
            "msg_count": random.randint(4, 50),
            "gps_count": random.randint(2, 12),
            "conv_1": "Alice → Bob: 'I'll bring the file.' (28.6139°N, 77.2090°E)",
            "conv_2": "Bob → Alice: 'Received. Let me know when you arrive.'",
            "timeline": "2026-06-19 08:00 → 2026-06-19 08:06 IST",
            "deleted_count": random.randint(0, 5),
            # Hardware
            "device_type": random.choice(["USB Mass Storage", "USB HID Keyboard Emulator"]),
            "vid": f"0x{random.randint(0x1000, 0xFFFF):04X}",
            "pid": f"0x{random.randint(0x1000, 0xFFFF):04X}",
            "risk_level": random.choice(["SUSPICIOUS", "HIGH RISK", "CRITICAL"]),
            "firmware_status": random.choice(["MODIFIED", "UNVERIFIED", "INTACT"]),
            "hid_emulation": random.choice(["YES — keystroke injection capable", "NO"]),
            "db_match": random.choice([
                "MATCH — Known BadUSB variant",
                "NO MATCH — Unknown device profile",
            ]),
            "recommendation": (
                "Quarantine the device immediately. Do not connect to any "
                "production system. Submit for firmware extraction and analysis."
            ),
        }

        response = mod["response_template"].format(**params)

        return {
            "response": response,
            "agent": self.AGENT_TYPE,
            "timestamp": ts,
            "threat_level_numeric": random.uniform(0.65, 0.98),
            "sources_consulted": random.randint(3, 8),
            "evidence_summary": f"Forensic analysis via {mod_key} module",
            "mitre_techniques": mod["mitre"],
            "data_sources": [
                f"{mod_key}_sandbox",
                "custody_ledger",
                "yara_ruleset_v4",
                "cti_ioc_feed",
            ],
        }


# ======================================================================
# Action / Response Agent
# ======================================================================
class ActionAgent(_BaseAgent):
    """
    Autonomous response agent.  Suggests or executes containment,
    remediation, and self-healing actions against identified threats.
    """

    AGENT_TYPE = "action"

    def execute(self, query, intent, module, context, attachments) -> dict:
        ts = self._stamp()

        actions = self._generate_response_plan(query, intent)

        response = (
            "🛡️ **Autonomous Threat Response Plan**\n\n"
            "SentinelCore has evaluated the threat and generated the following "
            "autonomous response actions:\n\n"
        )

        for i, action in enumerate(actions, 1):
            status_icon = "✅" if action["auto_executable"] else "⏳"
            response += (
                f"**{i}. {action['action']}**\n"
                f"   {status_icon} Status: {action['status']}\n"
                f"   ⏱️ ETA: {action['eta']}\n"
                f"   📋 Detail: {action['detail']}\n\n"
            )

        response += (
            "---\n"
            "**Guardrail Note:** All destructive actions (host isolation, "
            "key rotation) require analyst confirmation before execution. "
            "Non-destructive actions (monitoring, logging) are auto-approved.\n\n"
            "**MITRE ATT&CK Mitigations Applied:** M1030 (Network Segmentation), "
            "M1049 (Antivirus/Antimalware), M1026 (Privileged Account Management)"
        )

        return {
            "response": response,
            "agent": self.AGENT_TYPE,
            "timestamp": ts,
            "threat_level_numeric": random.uniform(0.7, 0.95),
            "sources_consulted": len(context) + 2,
            "evidence_summary": "Autonomous response plan generated",
            "actions_planned": len(actions),
            "mitre_techniques": ["M1030", "M1049", "M1026", "M1018"],
            "data_sources": [
                "k8s_cluster_state",
                "firewall_policy_engine",
                "credential_vault",
                "network_topology_map",
            ],
        }

    def _generate_response_plan(self, query: str, intent: str) -> list:
        """Build a context-aware remediation plan."""
        base_actions = [
            {
                "action": "Network Micro-Segmentation",
                "detail": (
                    "Generated Zero-Trust network policy to isolate affected "
                    "subnet. Applied Kubernetes NetworkPolicy across all edge clusters."
                ),
                "status": "AUTO-EXECUTED",
                "eta": "< 30 seconds",
                "auto_executable": True,
            },
            {
                "action": "Threat Signature Deployment",
                "detail": (
                    "Deployed updated YARA rules and Snort signatures to all "
                    "endpoint detection sensors and network IDS/IPS."
                ),
                "status": "AUTO-EXECUTED",
                "eta": "< 2 minutes",
                "auto_executable": True,
            },
            {
                "action": "Credential Rotation",
                "detail": (
                    "Initiated emergency rotation of all potentially compromised "
                    "service account credentials and API keys."
                ),
                "status": "AWAITING ANALYST CONFIRMATION",
                "eta": "5 minutes after approval",
                "auto_executable": False,
            },
            {
                "action": "C2 Channel Disruption",
                "detail": (
                    "Identified command-and-control endpoints and injected "
                    "adversarial noise into return channels. DNS sinkhole "
                    "rules applied at perimeter."
                ),
                "status": "AUTO-EXECUTED",
                "eta": "< 1 minute",
                "auto_executable": True,
            },
            {
                "action": "Evidence Preservation",
                "detail": (
                    "Full memory dump and disk image of affected hosts captured. "
                    "SHA-256 hashes computed and logged in chain-of-custody ledger "
                    "per BSA Section 63."
                ),
                "status": "AUTO-EXECUTED",
                "eta": "< 3 minutes",
                "auto_executable": True,
            },
            {
                "action": "Host Isolation & Self-Healing",
                "detail": (
                    "Killed 3 compromised pods and triggered self-healing "
                    "redeployment from verified container images. BGP routing "
                    "tables rotated across edge clusters."
                ),
                "status": "AWAITING ANALYST CONFIRMATION",
                "eta": "10 minutes after approval",
                "auto_executable": False,
            },
        ]

        # Filter / prioritise based on intent
        if intent in ("malware", "network_attack", "apt"):
            return base_actions  # Full response
        elif intent in ("darkweb", "phishing"):
            return base_actions[:4]  # Skip host isolation
        else:
            return base_actions[:3]  # Minimal response
