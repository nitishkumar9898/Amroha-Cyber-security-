"""
Incident Reporting & Dashboard Statistics Service
Generates CERT-IN style incident reports and aggregated dashboard metrics.
"""

import hashlib
import os
from datetime import datetime, timedelta
import random


class ReportService:

    THREAT_CATEGORIES = [
        "APT Intrusion", "Ransomware Deployment", "Deepfake Disinformation",
        "Data Exfiltration", "Credential Phishing", "Supply Chain Attack",
        "DDoS Infrastructure", "Mobile Spyware"
    ]

    AFFECTED_SECTORS = [
        "Defense & Aerospace", "Banking & Finance", "Power Grid Infrastructure",
        "Government e-Services", "Telecom Networks", "Healthcare Systems"
    ]

    @staticmethod
    def generate_incident_report(scenario_name: str, threat_actor: str, sector: str, analyst_name: str) -> dict:
        """Generate a structured CERT-IN style incident report."""
        now = datetime.now()
        incident_id = f"CERT-IN-{now.strftime('%Y')}-{random.randint(10000, 99999)}"
        detection_time = (now - timedelta(hours=random.randint(2, 48))).strftime("%Y-%m-%d %H:%M:%S IST")

        iocs = [
            {"type": "IP", "value": f"185.220.{random.randint(100,255)}.{random.randint(1,254)}", "confidence": "HIGH"},
            {"type": "SHA256", "value": hashlib.sha256(f"{threat_actor}-payload".encode()).hexdigest(), "confidence": "HIGH"},
            {"type": "DOMAIN", "value": f"{threat_actor.lower().replace(' ','-')}-c2.onion", "confidence": "MEDIUM"},
            {"type": "YARA", "value": f"rule {threat_actor.replace(' ','_')}_RAT {{ ... }}", "confidence": "HIGH"},
            {"type": "MITRE_ATT&CK", "value": f"T{random.randint(1000,1500)}.{random.randint(1,9):03d}", "confidence": "HIGH"},
        ]

        return {
            "incident_id": incident_id,
            "classification": "TLP:AMBER",
            "severity": "CRITICAL",
            "title": f"APT Campaign: {scenario_name}",
            "threat_actor": threat_actor,
            "affected_sector": sector,
            "detection_timestamp": detection_time,
            "report_generated": now.strftime("%Y-%m-%d %H:%M:%S IST"),
            "analyst": analyst_name,
            "agency": "CERT-IN / Indian Computer Emergency Response Team",
            "summary": (
                f"An advanced persistent threat actor identified as '{threat_actor}' was detected conducting a "
                f"multi-phase intrusion campaign targeting the {sector} sector. The attack vector involved "
                "deepfake-assisted social engineering, mobile device compromise, and dark web coordination "
                "channels. Forensic evidence has been collected and preserved under Section 63 BSA 2023."
            ),
            "attack_phases": [
                {"phase": 1, "name": "Initial Access", "technique": "Spear-Phishing with Deepfake Audio Lure", "mitre": "T1566.001"},
                {"phase": 2, "name": "Persistence", "technique": "Registry Run Keys / Startup Folder", "mitre": "T1547.001"},
                {"phase": 3, "name": "Lateral Movement", "technique": "Pass-the-Hash via Mimikatz", "mitre": "T1550.002"},
                {"phase": 4, "name": "Collection", "technique": "Data Staged on Removable Media", "mitre": "T1025"},
                {"phase": 5, "name": "Exfiltration", "technique": "Tor-based C2 over Encrypted Channel", "mitre": "T1048.001"},
            ],
            "iocs": iocs,
            "recommendations": [
                "Immediately isolate affected network segments and revoke compromised credentials.",
                "Deploy YARA rules across endpoint detection platforms within 2 hours.",
                "Block listed IOC IPs and domains at perimeter firewall and DNS-sinkhole.",
                "Notify CERT-IN via incidentreport@cert-in.org.in within 6 hours per DPDP Act 2023 mandate.",
                "Preserve all evidence under chain-of-custody per Section 63 BSA 2023 before remediation.",
                "Conduct mandatory post-incident review within 30 days for lessons-learned documentation.",
            ],
            "legal_reference": "Section 63, Bharatiya Sakshya Adhiniyam 2023 | DPDP Act 2023 | IT Act Section 66",
        }

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Return live aggregated platform statistics."""
        now = datetime.now()
        return {
            "platform": "CyberThreatForge v2.0",
            "generated_at": now.isoformat(),
            "threats_detected": random.randint(7, 14),
            "scenarios_run": random.randint(3, 8),
            "evidence_items": 4,
            "bsa_certs_issued": random.randint(1, 6),
            "active_modules": 7,
            "backend_uptime_hours": round((now - datetime(2026, 6, 19, 5, 0, 0)).total_seconds() / 3600, 1),
            "threat_trend": [
                {"hour": f"{i:02d}:00", "count": random.randint(0, 5)}
                for i in range(8, now.hour + 1)
            ],
            "top_threat_actors": [
                {"name": "APT-Shadow-Agent-01", "incidents": 4, "severity": "CRITICAL"},
                {"name": "LazarusGroup-IN", "incidents": 2, "severity": "HIGH"},
                {"name": "SideWinder-APT", "incidents": 1, "severity": "HIGH"},
            ],
            "module_usage": {
                "deepfake": random.randint(3, 12),
                "malware": random.randint(2, 9),
                "mobile": random.randint(4, 15),
                "darkweb": random.randint(1, 7),
                "psychology": random.randint(2, 8),
                "hardware": random.randint(1, 5),
            }
        }

    @staticmethod
    def get_activity_log() -> list:
        """Return a mock real-time activity log for the platform."""
        now = datetime.now()
        events = []
        activities = [
            ("INFO",    "User officer_sharma authenticated successfully", "AUTH"),
            ("SUCCESS", "Scenario run APT-Shadow-Agent-01 initialized", "SIMULATION"),
            ("SUCCESS", "Deepfake evidence analyzed: MANIPULATED (score 0.18)", "DEEPFAKE"),
            ("SUCCESS", "Malware sandbox executed: payload_sim.exe — CRITICAL severity", "MALWARE"),
            ("SUCCESS", "Mobile SQLite extracted: 5 messages with GPS coordinates", "MOBILE"),
            ("WARNING", "Dark web feed contains active exfiltration listing", "DARKWEB"),
            ("SUCCESS", "SHA-256 integrity verified: chat_history.db", "AUDIT"),
            ("ALERT",   "TAMPER DETECTED: chat_history.db hash mismatch", "TAMPER"),
            ("SUCCESS", "BSA Section 63 certificate issued for chat_history.db", "CERTIFY"),
            ("INFO",    "Hardware audit: USB device MOCK_USB_DUCKY_123 flagged SUSPICIOUS", "HARDWARE"),
            ("SUCCESS", "Psychology profile: HIGH urgency markers, threat score 0.87", "PSYCHOLOGY"),
            ("WARNING", "Misinformation claim evaluated: LOW credibility (score 0.19)", "MISINFO"),
            ("INFO",    "Full integrity audit completed across 4 evidence items", "AUDIT"),
        ]
        for i, (level, msg, category) in enumerate(activities):
            ts = (now - timedelta(minutes=len(activities) - i) * 3).strftime("%H:%M:%S")
            events.append({
                "timestamp": ts,
                "level": level,
                "category": category,
                "message": msg
            })
        return list(reversed(events))
