"""
Chain of Custody Ledger for CyberThreatForge
Implements cryptographic hash integrity checking and structured logging to comply
with standard forensic evidence rules (e.g., Indian Evidence Act / Bharatiya Sakshya Adhiniyam - BSA).
"""

import os
import hashlib
import json
from datetime import datetime

class CustodyLedger:
    def __init__(self, ledger_file="chain_of_custody.json"):
        self.ledger_file = ledger_file
        self.records = []
        self._load_ledger()

    def _load_ledger(self):
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except json.JSONDecodeError:
                self.records = []

    def _save_ledger(self):
        with open(self.ledger_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=4)

    def calculate_file_hash(self, filepath):
        """Calculates the SHA-256 hash of a file for integrity verification."""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except FileNotFoundError:
            return None

    def log_artifact(self, filepath, analyst_name, agency_id, description, action="COLLECTED"):
        """Logs an event in the chain of custody ledger, hashing the artifact."""
        file_hash = self.calculate_file_hash(filepath)
        if not file_hash:
            raise FileNotFoundError(f"Cannot locate evidence file: {filepath}")

        record = {
            "timestamp": datetime.now().isoformat(),
            "item_name": os.path.basename(filepath),
            "file_path": os.path.abspath(filepath),
            "sha256_hash": file_hash,
            "action": action,
            "officer_name": analyst_name,
            "agency_id": agency_id,
            "description": description,
            "entry_signature": ""
        }

        # Calculate dynamic entry signature to verify ledger state integrity
        record_str = f"{record['timestamp']}-{record['sha256_hash']}-{record['action']}-{record['agency_id']}"
        record["entry_signature"] = hashlib.sha256(record_str.encode('utf-8')).hexdigest()

        self.records.append(record)
        self._save_ledger()
        return record

    def verify_artifact_integrity(self, filepath):
        """Verifies if the current file hash matches the initial registered custody ledger hash."""
        current_hash = self.calculate_file_hash(filepath)
        if not current_hash:
            return False, "File not found"

        filename = os.path.basename(filepath)
        # Find the oldest entry (initial collection)
        initial_record = None
        for record in self.records:
            if record["item_name"] == filename and record["action"] == "COLLECTED":
                initial_record = record
                break

        if not initial_record:
            return False, "No collection record found in ledger"

        if initial_record["sha256_hash"] == current_hash:
            return True, "Hash verified successfully"
        else:
            return False, f"Hash mismatch! Expected: {initial_record['sha256_hash']}, Got: {current_hash}"

    def generate_bsa_certificate(self, filepath, analyst_designation="Cyber Forensic Examiner"):
        """Generates a mock certificate details structure mimicking Section 63 BSA (formerly Section 65B Indian Evidence Act)."""
        filename = os.path.basename(filepath)
        file_hash = self.calculate_file_hash(filepath)
        
        if not file_hash:
            return None

        certificate = {
            "legal_provision": "Section 63 of Bharatiya Sakshya Adhiniyam, 2023",
            "certification_date": datetime.now().strftime("%Y-%m-%d"),
            "evidence_name": filename,
            "sha256_checksum": file_hash,
            "examiner_details": {
                "designation": analyst_designation,
                "verified_device": "CyberThreatForge Simulator Workstation"
            },
            "declaration": (
                f"I hereby declare that the electronic record '{filename}' was generated/processed "
                "under lawful control on the CyberThreatForge training system. "
                "The computer system was operating properly, and the integrity of the data "
                f"has been maintained as verified by SHA-256 hash value {file_hash}."
            )
        }
        return certificate
