from sqlalchemy.orm import Session
from ..models.globaljurix import JurisdictionMap, EvidenceProtocol, MLATCompliance, AgencyCollaborationLink
from ..schemas.globaljurix import JurisdictionRequest, EvidenceSharingRequest, MLATRequest, AgencyLinkRequest
from ..modules.globaljurix_engine import JurisdictionMapper, EvidencePackager, MLATChecker, CollabLinker

class GlobalJurixService:
    @staticmethod
    def map_jurisdiction(db: Session, payload: JurisdictionRequest) -> dict:
        result = JurisdictionMapper.map(payload.source_country, payload.target_country)
        
        jmap = JurisdictionMap(
            case_id=payload.case_id,
            source_country=payload.source_country,
            target_country=payload.target_country,
            primary_legal_framework=result["primary_legal_framework"],
            jurisdiction_conflict=result["jurisdiction_conflict"]
        )
        db.add(jmap)
        db.commit()
        
        return {
            "case_id": payload.case_id,
            "primary_legal_framework": result["primary_legal_framework"],
            "jurisdiction_conflict": result["jurisdiction_conflict"],
            "routing_advice": result["routing_advice"]
        }

    @staticmethod
    def package_evidence(db: Session, payload: EvidenceSharingRequest) -> dict:
        result = EvidencePackager.package(payload.raw_data_string)
        
        evidence = EvidenceProtocol(
            evidence_id=payload.evidence_id,
            file_hash=result["file_hash"],
            encryption_standard=result["encryption_standard"],
            is_compliant=result["is_compliant"]
        )
        db.add(evidence)
        db.commit()
        
        return {
            "evidence_id": payload.evidence_id,
            "file_hash": result["file_hash"],
            "encryption_standard": result["encryption_standard"],
            "is_compliant": result["is_compliant"]
        }

    @staticmethod
    def check_mlat(db: Session, payload: MLATRequest) -> dict:
        result = MLATChecker.check(payload.requesting_country, payload.receiving_country)
        
        mlat = MLATCompliance(
            requesting_country=payload.requesting_country,
            receiving_country=payload.receiving_country,
            treaty_status=result["treaty_status"],
            estimated_processing_days=result["estimated_processing_days"]
        )
        db.add(mlat)
        db.commit()
        
        return result

    @staticmethod
    def link_collabguard(db: Session, payload: AgencyLinkRequest) -> dict:
        result = CollabLinker.link(payload.case_id, payload.agency_code)
        
        link = AgencyCollaborationLink(
            case_id=payload.case_id,
            agency_code=payload.agency_code,
            link_status=result["status"]
        )
        db.add(link)
        db.commit()
        
        return result
