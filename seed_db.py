"""
Database Seeder for CyberThreatForge
Populates SQLite/PostgreSQL databases with mock users, completed historical scenario runs,
and sample chain of custody logs to provide an immediate active range experience.
"""

import sys
import os
from datetime import datetime, timedelta

# Adjust path to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend", "app"))

from database import engine, SessionLocal, Base
import models

def seed_database():
    print("[*] Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if database is already seeded
        user_exists = db.query(models.DBUser).first()
        if user_exists:
            print("[+] Database already contains data. Skipping seeding.")
            return

        print("[*] Seeding mock users...")
        users = [
            models.DBUser(
                username="officer_sharma",
                hashed_password="secure_pass_2026",
                role="investigator",
                agency="CYBER-UNIT-DELHI"
            ),
            models.DBUser(
                username="director_patel",
                hashed_password="admin_secret_2026",
                role="admin",
                agency="NIA-HQ"
            ),
            models.DBUser(
                username="analyst_verma",
                hashed_password="analyst_password_2026",
                role="analyst",
                agency="CERT-In"
            )
        ]
        db.add_all(users)

        print("[*] Seeding historical simulation scenario runs...")
        historical_runs = [
            models.DBScenarioRun(
                scenario_id="SCENARIO-2026-01",
                name="Ransomware Extortion Simulation",
                threat_actor="APT-Phish-Group",
                target_sector="Healthcare Services",
                status="COMPLETED",
                start_time=datetime.utcnow() - timedelta(days=5),
                completed_phases="Intrusion Log Generation,Deepfake Authentication Validation,Mobile Chats Extraction,Dark Web Monitoring Intel"
            ),
            models.DBScenarioRun(
                scenario_id="SCENARIO-2026-02",
                name="Dynamic Model Injection Audit",
                threat_actor="APT-Shadow-Agent-01",
                target_sector="Defense Research Development",
                status="RUNNING",
                start_time=datetime.utcnow() - timedelta(hours=6),
                completed_phases="Intrusion Log Generation"
            )
        ]
        db.add_all(historical_runs)

        print("[*] Seeding sample Chain of Custody evidence log records...")
        sample_logs = [
            models.DBCustodyRecord(
                timestamp=datetime.utcnow() - timedelta(days=5),
                item_name="firewall_dump.pcap",
                file_path="/var/forensics/evidence/firewall_dump.pcap",
                sha256_hash="5e883f8271099a4e363c202f061d15b5f10b5b00c6c406bc0c306636706e232e",
                action="COLLECTED",
                officer_name="Inspector Sharma",
                agency_id="CYBER-UNIT-DELHI",
                description="Simulated raw traffic capture containing scanning packets.",
                entry_signature="0b35528c0dbd34a413d72ffc4cf6d7cfb56c808bd7c030c5e317c2f6d0fba20b"
            )
        ]
        db.add_all(sample_logs)

        db.commit()
        print("[+] Seeding complete. Core credentials and range history populated successfully.")

    except Exception as e:
        db.rollback()
        print(f"[!] Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
