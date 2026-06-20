import logging
from sqlalchemy.orm import Session
from ..models.training import TrainingSession, TrainingResult
from ..schemas import TrainingSessionCreate, TrainingResultCreate

logger = logging.getLogger(__name__)

class TrainingService:
    @staticmethod
    def start_session(db: Session, payload: TrainingSessionCreate) -> TrainingSession:
        session = TrainingSession(
            user_id=payload.user_id,
            scenario_name=payload.scenario_name,
            config=payload.config,
            status="IN_PROGRESS",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info("Started training session %s for user %s", session.id, session.user_id)
        return session

    @staticmethod
    def submit_result(db: Session, payload: TrainingResultCreate) -> TrainingResult:
        result = TrainingResult(
            session_id=payload.session_id,
            metric_name=payload.metric_name,
            metric_value=payload.metric_value,
            details=payload.details,
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        logger.info(
            "Recorded result for session %s: %s = %s",
            result.session_id,
            result.metric_name,
            result.metric_value,
        )
        return result

    @staticmethod
    def get_results(db: Session, session_id: int):
        return db.query(TrainingResult).filter(TrainingResult.session_id == session_id).all()

    @staticmethod
    def complete_session(db: Session, session_id: int, status: str = "COMPLETED"):
        sess = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        if sess:
            sess.status = status
            db.commit()
            db.refresh(sess)
        return sess

    @staticmethod
    def get_session(db: Session, session_id: int):
        return db.query(TrainingSession).filter(TrainingSession.id == session_id).first()

    @staticmethod
    def list_user_sessions(db: Session, user_id: int):
        return db.query(TrainingSession).filter(TrainingSession.user_id == user_id).all()

    @staticmethod
    def calculate_score(db: Session, session_id: int) -> float:
        """Calculate a total score for a training session.
        Currently, it simply sums all numeric metric values.
        Future versions could apply weighting or penalties.
        """
        results = TrainingService.get_results(db, session_id)
        total = sum(float(r.metric_value) for r in results if isinstance(r.metric_value, (int, float)))
        return total

    @staticmethod
    def get_hints(db: Session, session_id: int) -> list:
        """Retrieve scenario hints from the session's config.
        The config JSON stored in TrainingSession may contain a "hints" list.
        """
        session = TrainingService.get_session(db, session_id)
        if session and session.config and isinstance(session.config, dict):
            return session.config.get("hints", [])
        return []
