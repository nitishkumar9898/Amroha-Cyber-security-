from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.swarmforge import SwarmSimRequest, SwarmSimResult, AgentBehaviorReport, CounterSwarmRequest, CounterSwarmResult
from ..services.swarmforge_service import SwarmForgeService

router = APIRouter()

@router.post("/simulate-attack", response_model=SwarmSimResult)
def simulate_attack(payload: SwarmSimRequest, db: Session = Depends(get_db)):
    try:
        return SwarmForgeService.simulate_attack(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze-behavior/{sim_id}", response_model=AgentBehaviorReport)
def analyze_behavior(sim_id: int, db: Session = Depends(get_db)):
    try:
        return SwarmForgeService.analyze_behavior(db, sim_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deploy-counter-swarm", response_model=CounterSwarmResult)
def deploy_counter_swarm(payload: CounterSwarmRequest, db: Session = Depends(get_db)):
    try:
        return SwarmForgeService.deploy_counter_swarm(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
