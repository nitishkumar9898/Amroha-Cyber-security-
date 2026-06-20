import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self):
        self.models = {}

    async def register_model(self, model_id: str, version: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registers a new model version and tracks hyperparameters/metrics.
        """
        if model_id not in self.models:
            self.models[model_id] = []
            
        entry = {
            "version": version,
            "metrics": metrics,
            "status": "staged"
        }
        self.models[model_id].append(entry)
        
        logger.info(f"Registered {model_id} version {version}.")
        return entry

    async def promote_model(self, model_id: str, version: str) -> bool:
        """
        Promotes a model to production.
        """
        if model_id in self.models:
            for m in self.models[model_id]:
                if m["version"] == version:
                    m["status"] = "production"
                    return True
        return False

model_registry = ModelRegistry()
