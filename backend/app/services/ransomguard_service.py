import datetime
import json
import hashlib
from sqlalchemy.orm import Session

from ..models.ransomguard import RansomwareIncident, CryptoWallet, TransactionTrace, ForensicEvidence
from ..schemas.ransomguard import IncidentCreate, TraceRequest
from ..modules.ransomguard_engine import BlockchainAnalyzer, VariantDetector, AttributionEngine
# OSINT Integration (Mock dependency import pattern used in the app)
from .osint_service import OSINTForgeService

class RansomGuardService:
    
    @staticmethod
    def report_incident(db: Session, payload: IncidentCreate) -> RansomwareIncident:
        incident = RansomwareIncident(
            target_entity=payload.target_entity,
            ransom_note=payload.ransom_note,
            demanded_amount=payload.demanded_amount,
            currency=payload.currency,
            status="OPEN"
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def trace_crypto(db: Session, payload: TraceRequest) -> dict:
        incident = db.query(RansomwareIncident).filter(RansomwareIncident.id == payload.incident_id).first()
        if not incident:
            raise ValueError("Incident not found")
            
        incident.status = "TRACING"
        db.commit()

        # 1. AI Blockchain Trace
        trace_data = BlockchainAnalyzer.trace_wallet(payload.initial_wallet_address, incident.demanded_amount)
        
        # Save Wallets
        saved_wallets = []
        for w in trace_data["wallets"]:
            wallet = CryptoWallet(
                incident_id=incident.id,
                address=w["address"],
                wallet_type=w["wallet_type"],
                balance=w["balance"]
            )
            db.add(wallet)
            saved_wallets.append(wallet)
            
        # Save Traces
        saved_traces = []
        for t in trace_data["traces"]:
            trace = TransactionTrace(
                incident_id=incident.id,
                from_address=t["from"],
                to_address=t["to"],
                amount=t["amount"],
                risk_score=t["risk_score"]
            )
            db.add(trace)
            saved_traces.append(trace)
            
        db.commit()
        
        # 2. Variant Detection
        variant_info = VariantDetector.analyze_ransom_note(incident.ransom_note)
        
        # 3. Attribution
        cashout_wallet = next((w["address"] for w in trace_data["wallets"] if w["wallet_type"] == "CASH_OUT"), "unknown")
        attribution = AttributionEngine.attribute(variant_info["variant"], cashout_wallet)
        
        # 4. OSINT Integration
        # Check if the cashout wallet has dark web mentions
        # We mock this by generating an AI summary via the existing OSINT service
        try:
            osint_summary = OSINTForgeService.generate_ai_summary(db, f"wallet {cashout_wallet}")
        except Exception:
            osint_summary = "No OSINT intelligence available for this address."

        return {
            "incident_id": incident.id,
            "wallets_identified": trace_data["wallets"],
            "transaction_graph": trace_data["traces"],
            "variant_analysis": variant_info,
            "attribution": attribution,
            "osint_summary": osint_summary
        }

    @staticmethod
    def generate_compliance_report(db: Session, incident_id: int) -> dict:
        incident = db.query(RansomwareIncident).filter(RansomwareIncident.id == incident_id).first()
        if not incident:
            raise ValueError("Incident not found")
            
        wallets = db.query(CryptoWallet).filter(CryptoWallet.incident_id == incident_id).all()
        traces = db.query(TransactionTrace).filter(TransactionTrace.incident_id == incident_id).all()
        
        evidence_payload = {
            "incident_id": incident.id,
            "target": incident.target_entity,
            "reported_at": str(incident.reported_at),
            "wallets_traced": [w.address for w in wallets],
            "transaction_hops": len(traces)
        }
        
        # Create a digital signature/hash of the evidence for chain of custody
        evidence_json = json.dumps(evidence_payload, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
        
        evidence_record = ForensicEvidence(
            incident_id=incident.id,
            evidence_type="CHAIN_OF_CUSTODY_REPORT",
            data=evidence_payload,
            digital_signature=evidence_hash
        )
        db.add(evidence_record)
        db.commit()
        db.refresh(evidence_record)
        
        return {
            "incident_id": incident.id,
            "chain_of_custody_hash": evidence_hash,
            "evidence_logs": [evidence_payload],
            "generated_at": evidence_record.created_at
        }
