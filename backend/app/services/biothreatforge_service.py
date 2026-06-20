from sqlalchemy.orm import Session
from ..models.biothreatforge import GenomicSequence, SyntheticPathogenAnalysis, BioFacilitySecurity
from ..schemas.biothreatforge import SequenceAnalysisRequest, FacilityMonitorRequest
from ..modules.biothreatforge_engine import GenomicThreatAnalyzer, SynthesisFacilityMonitor

class BioThreatForgeService:
    @staticmethod
    def analyze_sequence(db: Session, payload: SequenceAnalysisRequest) -> dict:
        sequence = GenomicSequence(
            sequence_id=payload.sequence_id,
            sequence_hash=payload.sequence_hash,
            source_facility=payload.source_facility
        )
        db.add(sequence)
        
        analysis_data = GenomicThreatAnalyzer.analyze()
        
        analysis_record = SyntheticPathogenAnalysis(
            sequence_id=payload.sequence_id,
            bioweapon_probability=analysis_data["bioweapon_probability"],
            pathogenic_markers_found=analysis_data["pathogenic_markers_found"],
            is_threat=analysis_data["is_threat"]
        )
        db.add(analysis_record)
        db.commit()
        
        return {
            "sequence_id": payload.sequence_id,
            **analysis_data
        }

    @staticmethod
    def monitor_facility(db: Session, payload: FacilityMonitorRequest) -> dict:
        monitor_data = SynthesisFacilityMonitor.monitor()
        
        security_record = BioFacilitySecurity(
            facility_id=payload.facility_id,
            scada_anomaly_score=monitor_data["scada_anomaly_score"],
            unauthorized_prints_detected=monitor_data["unauthorized_prints_detected"],
            is_compromised=monitor_data["is_compromised"]
        )
        db.add(security_record)
        db.commit()
        
        return {
            "facility_id": payload.facility_id,
            **monitor_data
        }
