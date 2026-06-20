import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        pass

    async def check_drift(self, model_id: str, recent_accuracy: float) -> Dict[str, Any]:
        """
        Monitors model drift and triggers retraining if threshold crossed.
        """
        threshold = 0.85
        drift_detected = recent_accuracy < threshold
        
        logger.info(f"Checking drift for {model_id}: Accuracy={recent_accuracy}, Threshold={threshold}")
        
        return {
            "model_id": model_id,
            "drift_detected": drift_detected,
            "recent_accuracy": recent_accuracy,
            "action": "trigger_retraining" if drift_detected else "continue_monitoring"
        }

performance_monitor = PerformanceMonitor()
