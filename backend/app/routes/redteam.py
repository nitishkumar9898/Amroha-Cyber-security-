from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.redteam import ScenarioCreate, ScenarioResponse, SimulationStart, SimulationStatusResponse, ActionSubmit, AnalysisReportResponse
from ..services.redteam_service import RedTeamService

router = APIRouter()

@router.post("/scenarios/generate", response_model=ScenarioResponse)
def generate_scenario(payload: ScenarioCreate, db: Session = Depends(get_db)):
    """Generate an automated red team scenario using agentic AI simulation."""
    try:
        scenario = RedTeamService.generate_scenario(db, payload)
        return scenario
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulation/start", response_model=SimulationStatusResponse)
def start_simulation(payload: SimulationStart, db: Session = Depends(get_db)):
    """Start a Blue vs Red team collaborative simulation run."""
    try:
        run = RedTeamService.start_simulation(db, payload)
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulation/{run_id}/action")
def submit_action(run_id: int, payload: ActionSubmit, db: Session = Depends(get_db)):
    """Submit an action for either the blue or red team."""
    try:
        result = RedTeamService.submit_action(db, run_id, payload)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/simulation/{run_id}/analysis", response_model=AnalysisReportResponse)
def get_analysis(run_id: int, db: Session = Depends(get_db)):
    """Retrieve post-exercise analysis and recommendations."""
    try:
        report = RedTeamService.get_analysis(db, run_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
