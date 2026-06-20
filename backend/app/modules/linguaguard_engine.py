from typing import Dict, Any

def analyze_and_translate(language: str, text: str) -> Dict[str, Any]:
    """
    Simulates multilingual threat intelligence translation and intent scoring.
    """
    # Dummy translation
    translated = f"[Translated from {language}] Possible reference to an attack on the power grid."
    
    # Simple keyword heuristic
    threat_score = 0.85 if "attack" in translated.lower() or "grid" in translated.lower() else 0.30
    
    return {
        "translated_text": translated,
        "threat_intent_score": threat_score
    }
