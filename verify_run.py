"""
Interactive Training & Simulation Dashboard for CyberThreatForge
Allows users to run scenarios, generate artifacts, verify integrity,
and export legal forensic certificates.
"""

import os
import sys
import json
from scenario_engine import ThreatScenario, ScenarioPhase
from artifact_generator import ForensicArtifactGenerator
from custody_ledger import CustodyLedger

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("=" * 65)
    print(f" {title.upper()} ".center(65, "="))
    print("=" * 65)

def main():
    output_dir = "./forensic_evidence"
    os.makedirs(output_dir, exist_ok=True)
    
    generator = ForensicArtifactGenerator(output_dir)
    ledger = CustodyLedger(ledger_file=os.path.join(output_dir, "chain_of_custody.json"))
    
    # Pre-populate dynamic threat scenario
    scenario = ThreatScenario(
        scenario_id="SCENARIO-2026-FUTURE",
        name="APT Autonomous Model Poisoning & Espionage Simulation",
        threat_actor="APT-Shadow-Agent-01",
        target_sector="Defense Research Development"
    )
    scenario.add_phase(ScenarioPhase("Intrusion Log Generation", "Creates mock network logs representing initial entry.", 0))
    scenario.add_phase(ScenarioPhase("Deepfake Authentication Validation", "Evaluates metadata of synthesized video proofs.", 0))
    scenario.add_phase(ScenarioPhase("Mobile Chats Extraction", "Extracts location-tagged chat transcripts from SQLite.", 0))
    scenario.add_phase(ScenarioPhase("Dark Web Monitoring Intel", "Scrapes anonymous forums for matching credentials.", 0))
    scenario.start()

    while True:
        clear_screen()
        print_header("CyberThreatForge: Forensic Range & Threat Simulator")
        print(f"Active Scenario: {scenario.name}")
        print(f"Threat Actor   : {scenario.threat_actor}")
        print(f"Target Sector  : {scenario.target_sector}")
        print(f"Overall Status : {scenario.status}")
        print("-" * 65)
        print(" [1] Initialize / Re-generate All Simulation Artifacts")
        print(" [2] View Active Scenario Timeline & Phases Status")
        print(" [3] Run Integrity Check on Evidence (Tamper Detection)")
        print(" [4] Intentionally Tamper with Evidence File (Demo)")
        print(" [5] Inspect Simulated Mobile Forensics Chat & GPS Data")
        print(" [6] Analyze Simulated Deepfake Manipulation Metadata")
        print(" [7] Inspect Simulated Dark Web Marketplace Intel")
        print(" [8] Generate Section 63 BSA Digital Forensic Certificate")
        print(" [0] Exit Simulator")
        print("-" * 65)
        
        choice = input("Select an option (0-8): ").strip()
        
        if choice == "1":
            clear_screen()
            print_header("Generating Forensic Evidence Artifacts")
            
            print("[*] Generating web logs...")
            web_log = generator.generate_web_access_logs()
            ledger.log_artifact(web_log, "Inspector R. Sharma", "CYBER-UNIT-DELHI", "Apache web logs showing simulated directory traversal.", "COLLECTED")
            scenario.mark_phase_complete("Intrusion Log Generation")
            
            print("[*] Generating media analysis JSON...")
            media_json = generator.generate_deepfake_metadata()
            ledger.log_artifact(media_json, "Inspector R. Sharma", "CYBER-UNIT-DELHI", "Synthetic media metadata deepfake analysis.", "COLLECTED")
            scenario.mark_phase_complete("Deepfake Authentication Validation")
            
            print("[*] Generating mobile sqlite db...")
            db_path = generator.generate_mobile_chat_db()
            ledger.log_artifact(db_path, "Inspector R. Sharma", "CYBER-UNIT-DELHI", "SQLite extraction database for mobile chat messages.", "COLLECTED")
            scenario.mark_phase_complete("Mobile Chats Extraction")

            print("[*] Scraping simulated dark web posts...")
            dw_json = generator.generate_darkweb_intel()
            ledger.log_artifact(dw_json, "Inspector R. Sharma", "CYBER-UNIT-DELHI", "Scraped dark web posts mentioning targeted organizations.", "COLLECTED")
            scenario.mark_phase_complete("Dark Web Monitoring Intel")
            
            print("\n[+] All simulation artifacts generated successfully under ./forensic_evidence/")
            print("[+] All hashes logged securely to chain_of_custody.json.")
            input("\nPress Enter to return to main menu...")
            
        elif choice == "2":
            clear_screen()
            print_header("Scenario Timeline & Phases")
            report = scenario.get_status_report()
            for phase in report["phases"]:
                status_str = "[COMPLETED]" if phase["completed"] else ("[ACTIVE]" if phase["is_active"] else "[PENDING]")
                print(f"Phase Name  : {phase['name']}")
                print(f"Description : {phase['description']}")
                print(f"Status      : {status_str}")
                print("-" * 40)
            input("\nPress Enter to return to main menu...")

        elif choice == "3":
            clear_screen()
            print_header("Forensic Evidence Integrity Check")
            files_to_check = ["web_access.log", "chat_history.db", "media_analysis.json", "darkweb_intel.json"]
            all_verified = True
            for fname in files_to_check:
                filepath = os.path.join(output_dir, fname)
                if not os.path.exists(filepath):
                    print(f"[-] Missing: {fname} (Run option 1 to generate)")
                    all_verified = False
                    continue
                verified, msg = ledger.verify_artifact_integrity(filepath)
                status_tag = "[OK]      " if verified else "[ALERT!!!]"
                print(f"{status_tag} {fname}: {msg}")
            
            input("\nPress Enter to return to main menu...")

        elif choice == "4":
            clear_screen()
            print_header("Simulate Tampering (Demonstration)")
            db_path = os.path.join(output_dir, "chat_history.db")
            if not os.path.exists(db_path):
                print("[-] chat_history.db does not exist. Please generate artifacts first (Option 1).")
            else:
                with open(db_path, "ab") as f:
                    f.write(b"\x00\x00\x00\x00")
                print("[+] Success: Appended trailing null bytes to 'chat_history.db'.")
                print("[*] Its SHA-256 hash has now changed. Run Integrity Check (Option 3) to witness detection.")
            input("\nPress Enter to return to main menu...")

        elif choice == "5":
            clear_screen()
            print_header("Mobile Chat Forensics Extract")
            db_path = os.path.join(output_dir, "chat_history.db")
            if not os.path.exists(db_path):
                print("[-] Database not found. Please run Option 1 first.")
            else:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, sender, receiver, message, timestamp, latitude, longitude FROM messages")
                rows = cursor.fetchall()
                print(f"{'ID':<4} | {'Sender':<8} | {'Receiver':<8} | {'Timestamp':<20} | {'Location':<22} | {'Message'}")
                print("-" * 100)
                for r in rows:
                    location = f"{r[4]}, {r[5]}" if r[4] else "N/A"
                    print(f"{r[0]:<4} | {r[1]:<8} | {r[2]:<8} | {r[4]:<20} | {f'{r[5]},{r[6]}':<22} | {r[3]}")
                conn.close()
            input("\nPress Enter to return to main menu...")

        elif choice == "6":
            clear_screen()
            print_header("Deepfake Manipulation Analysis Report")
            media_path = os.path.join(output_dir, "media_analysis.json")
            if not os.path.exists(media_path):
                print("[-] Analysis report file not found. Please run Option 1 first.")
            else:
                with open(media_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(json.dumps(data, indent=2))
            input("\nPress Enter to return to main menu...")

        elif choice == "7":
            clear_screen()
            print_header("Dark Web Threat Intelligence Feeds")
            dw_path = os.path.join(output_dir, "darkweb_intel.json")
            if not os.path.exists(dw_path):
                print("[-] Intelligence feed file not found. Please run Option 1 first.")
            else:
                with open(dw_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(json.dumps(data, indent=2))
            input("\nPress Enter to return to main menu...")

        elif choice == "8":
            clear_screen()
            print_header("Section 63 BSA Digital Certificate Generation")
            print("Select file to certify:")
            files = ["web_access.log", "chat_history.db", "media_analysis.json", "darkweb_intel.json"]
            for idx, f in enumerate(files):
                print(f" [{idx + 1}] {f}")
            sub_choice = input("Choice (1-4): ").strip()
            try:
                sel_fname = files[int(sub_choice) - 1]
                filepath = os.path.join(output_dir, sel_fname)
                if not os.path.exists(filepath):
                    print(f"[-] File {sel_fname} does not exist. Run Option 1 first.")
                else:
                    cert = ledger.generate_bsa_certificate(filepath, "Chief Scientific Examiner")
                    print("\nGenerated Certificate Details:")
                    print("-" * 65)
                    print(json.dumps(cert, indent=2))
            except (ValueError, IndexError):
                print("[-] Invalid choice.")
            input("\nPress Enter to return to main menu...")

        elif choice == "0":
            clear_screen()
            print("Exiting CyberThreatForge. Training session ended.")
            break
        else:
            input("\n[-] Invalid selection. Press Enter to retry...")

if __name__ == "__main__":
    main()
