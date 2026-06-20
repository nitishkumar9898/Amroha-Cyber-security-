from typing import Dict, Any

def detect_data_poisoning(dataset: str, sample_id: str) -> Dict[str, Any]:
    """
    Simulates adversarial AI data poisoning detection.
    """
    prob = 0.95 if "train" in dataset.lower() and "adv" in sample_id.lower() else 0.10
    perturbation = "Gradient-based label flip" if prob > 0.5 else "None"
    
    return {
        "poison_probability": prob,
        "perturbation_type": perturbation
    }
