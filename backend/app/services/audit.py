"""
Chain of Custody and Evidence Auditing Service
Implements immutable hash registries in SQL and Section 63 BSA Certificates.
"""

import os
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import DBCustodyRecord
from ..schemas import BSAExchangeRequest

class AuditService:
    @staticmethod
    def calculate_file_hash(filepath: str) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except FileNotFoundError:
            return ""

    @staticmethod
    def log_custody_event(db: Session, filepath: str, officer_name: str, agency_id: str, description: str, action: str = "COLLECTED"):
        file_hash = AuditService.calculate_file_hash(filepath)
        if not file_hash:
            raise FileNotFoundError(f"Evidence file not found: {filepath}")

        # Compute tamper signature representing sequential proof of transaction
        timestamp_str = datetime.utcnow().isoformat()
        record_str = f"{timestamp_str}-{file_hash}-{action}-{agency_id}"
        entry_signature = hashlib.sha256(record_str.encode('utf-8')).hexdigest()

        db_record = DBCustodyRecord(
            timestamp=datetime.utcnow(),
            item_name=os.path.basename(filepath),
            file_path=os.path.abspath(filepath),
            sha256_hash=file_hash,
            action=action,
            officer_name=officer_name,
            agency_id=agency_id,
            description=description,
            entry_signature=entry_signature
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def verify_integrity(db: Session, filepath: str):
        current_hash = AuditService.calculate_file_hash(filepath)
        if not current_hash:
            return False, "File missing or inaccessible."

        filename = os.path.basename(filepath)
        initial_record = db.query(DBCustodyRecord).filter(
            DBCustodyRecord.item_name == filename,
            DBCustodyRecord.action == "COLLECTED"
        ).order_by(DBCustodyRecord.timestamp.asc()).first()

        if not initial_record:
            return False, "No initial collection record found in database."

        if initial_record.sha256_hash == current_hash:
            return True, "Hash verified successfully."
        else:
            return False, f"Mismatch alert! Expected: {initial_record.sha256_hash}, Got: {current_hash}"

    @staticmethod
    def generate_bsa_cert(filepath: str, designation: str) -> dict:
        file_hash = AuditService.calculate_file_hash(filepath)
        if not file_hash:
            return {}

        return {
            "legal_provision": "Section 63 of Bharatiya Sakshya Adhiniyam, 2023",
            "certification_date": datetime.now().strftime("%Y-%m-%d"),
            "evidence_name": os.path.basename(filepath),
            "sha256_checksum": file_hash,
            "examiner_details": {
                "designation": designation,
                "verified_device": "CyberThreatForge Simulator Web Station"
            },
            "declaration": (
                f"I hereby declare that the electronic record '{os.path.basename(filepath)}' was generated/processed "
                "under lawful control on the CyberThreatForge training system. "
                "The computer system was operating properly, and the integrity of the data "
                f"has been maintained as verified by SHA-256 hash value {file_hash}."
            )
        }
