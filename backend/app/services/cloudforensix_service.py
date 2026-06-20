from sqlalchemy.orm import Session
from ..models.cloudforensix import CloudIncident, CloudLogEvidence, ContainerForensicRecord, ServerlessTrace
from ..schemas.cloudforensix import IncidentCreate, LogAnalysisRequest, ContainerScanRequest, ServerlessTraceRequest
from ..modules.cloudforensix_engine import MultiCloudLogAnalyzer, OrchestrationScanner, ServerlessTracer, DataResidencyChecker

class CloudForensixService:
    
    @staticmethod
    def report_incident(db: Session, payload: IncidentCreate) -> CloudIncident:
        incident = CloudIncident(provider=payload.provider, severity=payload.severity)
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def analyze_logs(db: Session, payload: LogAnalysisRequest) -> dict:
        incident = db.query(CloudIncident).filter(CloudIncident.id == payload.incident_id).first()
        if not incident:
            raise ValueError("Incident not found")
            
        analysis = MultiCloudLogAnalyzer.analyze(payload.raw_logs)
        
        # Save Evidences
        for res in analysis["results"]:
            evidence = CloudLogEvidence(
                incident_id=incident.id,
                log_source=payload.log_source,
                raw_log=res["log"],
                is_anomalous=res["is_anomalous"],
                anomaly_score=res["score"],
                findings=res["finding"]
            )
            db.add(evidence)
            
        # Optional Integration: If anomalous, we would ideally escalate to ResponseForge ActionLog here
        # E.g., ResponseForgeService.log_action("Cloud Anomaly Escalated", incident.id)
            
        db.commit()
        
        return {
            "incident_id": incident.id,
            "analyzed_count": analysis["analyzed_count"],
            "anomalies_detected": analysis["anomalies_detected"],
            "findings": analysis["findings"]
        }

    @staticmethod
    def scan_container(db: Session, payload: ContainerScanRequest) -> dict:
        incident = db.query(CloudIncident).filter(CloudIncident.id == payload.incident_id).first()
        if not incident:
            raise ValueError("Incident not found")
            
        scan_result = OrchestrationScanner.scan(payload.image_hash, payload.namespace)
        
        record = ContainerForensicRecord(
            incident_id=incident.id,
            image_hash=scan_result["image_hash"],
            namespace=payload.namespace,
            escape_detected=scan_result["escape_detected"],
            vulnerabilities=scan_result["vulnerabilities"]
        )
        db.add(record)
        db.commit()
        
        return {
            "incident_id": incident.id,
            "image_hash": scan_result["image_hash"],
            "escape_detected": scan_result["escape_detected"],
            "vulnerabilities": scan_result["vulnerabilities"]
        }

    @staticmethod
    def trace_serverless(db: Session, payload: ServerlessTraceRequest) -> dict:
        incident = db.query(CloudIncident).filter(CloudIncident.id == payload.incident_id).first()
        if not incident:
            raise ValueError("Incident not found")
            
        trace_result = ServerlessTracer.trace(payload.function_name)
        
        trace = ServerlessTrace(
            incident_id=incident.id,
            function_name=trace_result["function_name"],
            execution_path=trace_result["execution_path"],
            duration_ms=120.5, # mock duration
            contains_malicious_payload=trace_result["malicious_payload_detected"]
        )
        db.add(trace)
        db.commit()
        
        return {
            "incident_id": incident.id,
            "function_name": trace_result["function_name"],
            "execution_path": trace_result["execution_path"],
            "malicious_payload_detected": trace_result["malicious_payload_detected"]
        }

    @staticmethod
    def check_residency(db: Session, incident_id: int) -> dict:
        # Retrieve all logs associated with the incident to check for data residency violations
        evidences = db.query(CloudLogEvidence).filter(CloudLogEvidence.incident_id == incident_id).all()
        raw_logs = [e.raw_log for e in evidences if e.raw_log]
        
        residency_result = DataResidencyChecker.check(raw_logs)
        
        return {
            "incident_id": incident_id,
            "is_compliant": residency_result["is_compliant"],
            "violations": residency_result["violations"]
        }
