from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import firmwareguard_models as models
from ..schemas import firmwareguard_schemas as schemas
from ..modules import firmwareguard_engine as engine

router = APIRouter(prefix="/firmwareguard", tags=["FirmwareGuard"])

@router.post("/firmware", response_model=schemas.FirmwareRead)
def upload_firmware(firmware: schemas.FirmwareCreate, db: Session = Depends(get_db)):
    db_firmware = models.FirmwareImage(**firmware.dict())
    db.add(db_firmware)
    db.commit()
    db.refresh(db_firmware)
    return db_firmware

@router.get("/firmware", response_model=List[schemas.FirmwareRead])
def get_firmwares(db: Session = Depends(get_db)):
    return db.query(models.FirmwareImage).all()

@router.post("/firmware/{firmware_id}/analyze", response_model=schemas.FirmwareAnalysisResult)
def analyze_firmware(firmware_id: int, db: Session = Depends(get_db)):
    firmware = db.query(models.FirmwareImage).filter(models.FirmwareImage.id == firmware_id).first()
    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
    result = engine.analyze_firmware(firmware.file_hash, firmware.is_signed)
    firmware.risk_score = result["risk_score"]
    firmware.status = result["status"]
    db.commit()
    
    return schemas.FirmwareAnalysisResult(
        firmware_id=firmware.id,
        risk_score=result["risk_score"],
        findings=result["findings"],
        status=result["status"]
    )
