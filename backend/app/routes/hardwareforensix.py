from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.hardwareforensix import FirmwareImage, SideChannelTrace
from app.schemas.hardwareforensix import FirmwareAnalysisOut, TraceAnalysisRequest, TraceAnalysisOut
from app.modules.hardwareforensix.image_analyzer import image_analyzer
from app.modules.hardwareforensix.side_channel_detector import side_channel_detector
from app.modules.hardwareforensix.firmware_re import firmware_re
from app.modules.hardwareforensix.hardware_sandbox import hardware_sandbox
from app.modules.hardwareforensix.cross_module_bridge import cross_module_bridge

router = APIRouter()

@router.post("/firmware/upload", response_model=FirmwareAnalysisOut)
async def upload_firmware(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    analysis = await image_analyzer.analyze_firmware_image(contents)
    
    db_image = FirmwareImage(
        filename=file.filename,
        sha256=analysis["sha256"],
        size_bytes=analysis["size_bytes"],
        entropy=analysis["entropy"],
        analysis_results={"components": analysis["components_detected"], "findings": analysis["findings"]}
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image

@router.post("/traces/analyze", response_model=TraceAnalysisOut)
async def analyze_trace(request: TraceAnalysisRequest, db: Session = Depends(get_db)):
    analysis = await side_channel_detector.detect_anomalies(request.data_points, request.trace_type)
    
    db_trace = SideChannelTrace(
        device_id=request.device_id,
        trace_type=request.trace_type,
        anomaly_score=analysis["anomaly_score"],
        is_attack=1 if analysis["attack_detected"] else 0
    )
    db.add(db_trace)
    db.commit()
    
    return analysis

@router.post("/firmware/re/{architecture}")
async def reverse_engineer_snippet(architecture: str, code: Dict[str, str]):
    snippet = code.get("code", "")
    analysis = await firmware_re.analyze_code_snippet(snippet, architecture)
    return analysis

@router.post("/firmware/sandbox/{firmware_id}")
async def detonate_firmware(firmware_id: str, architecture: str = "ARM"):
    trace = await hardware_sandbox.execute_firmware(firmware_id, architecture)
    
    # Cross-correlate after sandbox execution
    correlation = await cross_module_bridge.correlate_findings({"findings": trace["network_activity"]})
    trace["correlation"] = correlation
    
    return trace
