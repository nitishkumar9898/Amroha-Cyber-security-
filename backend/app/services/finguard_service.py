from sqlalchemy.orm import Session
from ..models.finguard import TransactionAnomaly, PaymentTrace, LaunderingPattern, ComplianceReport
from ..schemas.finguard import TransactionAnomalyRequest, PaymentTraceRequest, LaunderingPatternRequest, ComplianceReportRequest
from ..modules.finguard_engine import AnomalyDetector, PaymentTracer, LaunderingAnalyzer, ComplianceGenerator

class FinGuardService:
    @staticmethod
    def detect_anomaly(db: Session, payload: TransactionAnomalyRequest) -> dict:
        result = AnomalyDetector.detect(payload.amount, payload.velocity_score)
        
        anomaly = TransactionAnomaly(
            transaction_id=payload.transaction_id,
            amount=payload.amount,
            velocity_score=payload.velocity_score,
            is_anomalous=result["is_anomalous"]
        )
        db.add(anomaly)
        db.commit()
        
        return {
            "transaction_id": payload.transaction_id,
            "is_anomalous": result["is_anomalous"],
            "action_taken": result["action_taken"]
        }

    @staticmethod
    def trace_payment(db: Session, payload: PaymentTraceRequest) -> dict:
        result = PaymentTracer.trace(payload.hop_sequence)
        
        trace = PaymentTrace(
            trace_id=payload.trace_id,
            hop_count=len(payload.hop_sequence.split("->")),
            crosses_borders=result["crosses_borders"],
            complexity_score=result["complexity_score"]
        )
        db.add(trace)
        db.commit()
        
        return {
            "trace_id": payload.trace_id,
            "complexity_score": result["complexity_score"],
            "crosses_borders": result["crosses_borders"],
            "trace_status": result["trace_status"]
        }

    @staticmethod
    def analyze_laundering(db: Session, payload: LaunderingPatternRequest) -> dict:
        result = LaunderingAnalyzer.analyze(payload.transaction_count, payload.average_amount, payload.osint_threat_intel, payload.ransomware_watchlist)
        
        pattern = LaunderingPattern(
            entity_id=payload.entity_id,
            pattern_type=result["pattern_type"],
            osint_flagged=payload.osint_threat_intel,
            ransomware_linked=payload.ransomware_watchlist
        )
        db.add(pattern)
        db.commit()
        
        return {
            "entity_id": payload.entity_id,
            "pattern_type": result["pattern_type"],
            "risk_level": result["risk_level"]
        }

    @staticmethod
    def generate_compliance(db: Session, payload: ComplianceReportRequest) -> dict:
        result = ComplianceGenerator.generate(payload.agency, payload.raw_financial_data)
        
        report = ComplianceReport(
            report_id=result["report_id"],
            agency=payload.agency,
            report_hash=result["report_hash"]
        )
        db.add(report)
        db.commit()
        
        return {
            "report_id": result["report_id"],
            "agency": payload.agency,
            "report_hash": result["report_hash"],
            "submission_status": result["submission_status"]
        }
