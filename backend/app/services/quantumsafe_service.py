from sqlalchemy.orm import Session
from ..models.quantumsafe import CryptoAsset, PQCVulnerability, MigrationSimulation
from ..schemas.quantumsafe import PQCScanRequest, PQCScanResponse, AssetAnalysisResult, CryptoAssetRead, PQCVulnerabilityRead, MigrationSimulationRead
from ..modules.quantumsafe_engine import scan_legacy_crypto, calculate_hndl_risk, simulate_pqc_migration

def run_pqc_scan(db: Session, request: PQCScanRequest) -> PQCScanResponse:
    # 1. Scan for assets
    asset_dicts = scan_legacy_crypto(request.target_system, request.scan_id)
    
    # Clear old scan if same ID for idempotency in demo
    db.query(CryptoAsset).filter(CryptoAsset.scan_id == request.scan_id).delete()
    
    results = []
    
    for a_dict in asset_dicts:
        asset = CryptoAsset(
            scan_id=a_dict["scan_id"],
            asset_name=a_dict["asset_name"],
            algorithm=a_dict["algorithm"],
            key_size=a_dict["key_size"],
            is_quantum_safe=a_dict["is_quantum_safe"]
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        
        vuln = None
        mig = None
        
        # 2. Calculate Vulnerability
        v_dict = calculate_hndl_risk(a_dict)
        if v_dict:
            vuln = PQCVulnerability(
                asset_id=asset.id,
                hndl_risk_score=v_dict["hndl_risk_score"],
                estimated_qday_years=v_dict["estimated_qday_years"],
                criticality=v_dict["criticality"]
            )
            db.add(vuln)
            
            # 3. Simulate Migration
            m_dict = simulate_pqc_migration(a_dict)
            if m_dict:
                mig = MigrationSimulation(
                    asset_id=asset.id,
                    recommended_pqc=m_dict["recommended_pqc"],
                    legacy_latency_ms=m_dict["legacy_latency_ms"],
                    pqc_latency_ms=m_dict["pqc_latency_ms"],
                    memory_overhead_kb=m_dict["memory_overhead_kb"]
                )
                db.add(mig)
            
            db.commit()
            if vuln: db.refresh(vuln)
            if mig: db.refresh(mig)
            
        results.append(AssetAnalysisResult(
            asset=CryptoAssetRead.model_validate(asset, from_attributes=True),
            vulnerability=PQCVulnerabilityRead.model_validate(vuln, from_attributes=True) if vuln else None,
            migration=MigrationSimulationRead.model_validate(mig, from_attributes=True) if mig else None
        ))
        
    return PQCScanResponse(
        scan_id=request.scan_id,
        target_system=request.target_system,
        assets=results
    )
