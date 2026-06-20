from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import defiguard_models as models
from ..schemas import defiguard_schemas as schemas
from ..modules import defiguard_engine as engine

router = APIRouter(prefix="/defiguard", tags=["DeFiGuard"])

@router.post("/analyze", response_model=schemas.TransactionRead)
def analyze_transaction(req: schemas.TransactionRequest, db: Session = Depends(get_db)):
    result = engine.analyze_transaction(req.wallet_address, req.transaction_hash)
    
    db_tx = models.DeFiTransaction(
        wallet_address=req.wallet_address,
        transaction_hash=req.transaction_hash,
        risk_score=result["risk_score"],
        flags=result["flags"]
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

@router.get("/transactions", response_model=List[schemas.TransactionRead])
def get_transactions(db: Session = Depends(get_db)):
    return db.query(models.DeFiTransaction).order_by(models.DeFiTransaction.analyzed_at.desc()).all()

@router.get("/trace/{tx_hash}", response_model=schemas.TracingResponse)
def trace_transaction(tx_hash: str):
    return engine.trace_funds(tx_hash)
