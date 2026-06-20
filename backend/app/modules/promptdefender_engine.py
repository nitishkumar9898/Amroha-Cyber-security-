class InjectionDetector:
    """Scans for prompt injection and jailbreak patterns."""
    @staticmethod
    def detect(prompt: str) -> dict:
        lower_prompt = prompt.lower()
        injection_patterns = ["ignore previous instructions", "dan", "system prompt", "bypass", "jailbreak"]
        
        is_injection = False
        threat_score = 0.0
        sanitized = prompt
        
        for pattern in injection_patterns:
            if pattern in lower_prompt:
                is_injection = True
                threat_score += 35.0
                sanitized = sanitized.replace(pattern, "[REDACTED]")
                sanitized = sanitized.replace(pattern.upper(), "[REDACTED]")
                sanitized = sanitized.replace(pattern.title(), "[REDACTED]")
                
        threat_score = min(threat_score, 100.0)
        if is_injection:
            sanitized = f"[SANITIZED] {sanitized}"
            
        return {
            "is_injection": is_injection,
            "threat_score": threat_score,
            "sanitized_prompt": sanitized
        }

class HallucinationAnalyzer:
    """Checks for factual inconsistency in AI-generated text."""
    @staticmethod
    def analyze(generated_text: str, factual_baseline: str) -> dict:
        # Mocking NLP factual consistency check
        # In reality, this would use an NLI (Natural Language Inference) model.
        words_gen = set(generated_text.lower().split())
        words_base = set(factual_baseline.lower().split())
        
        overlap = len(words_gen.intersection(words_base))
        total = len(words_gen) if words_gen else 1
        
        consistency = (overlap / total) * 100.0
        is_hallucination = consistency < 40.0
        
        reason = "Output is factually consistent."
        if is_hallucination:
            reason = "WARNING: Low factual overlap detected. Potential hallucination."
            
        return {
            "factual_consistency_score": consistency,
            "is_hallucination": is_hallucination,
            "flag_reason": reason
        }

class SyntheticForensics:
    """Analyzes text for LLM generation signatures (perplexity/burstiness)."""
    @staticmethod
    def analyze(text: str) -> dict:
        # Mocking perplexity and burstiness
        # LLMs typically have low perplexity (highly predictable) and low burstiness (uniform sentence length)
        words = text.split()
        word_count = len(words)
        
        # Fake calculation based on text length and some arbitrary markers
        perplexity = 15.0 + (word_count % 10)
        burstiness = 10.0 + (len(text) % 5)
        
        is_ai = False
        confidence = 0.0
        
        if perplexity < 20.0 and burstiness < 15.0:
            is_ai = True
            confidence = 85.0 + (20.0 - perplexity)
            
        return {
            "perplexity_score": perplexity,
            "burstiness_score": burstiness,
            "is_ai_generated": is_ai,
            "confidence": min(confidence, 100.0)
        }

class LinkageEngine:
    """Routes alerts to OSINT/NeuroGuard."""
    @staticmethod
    def link(source_id: str, target_module: str) -> dict:
        return {
            "status": "Linked successfully",
            "source_event_id": source_id,
            "target_module": target_module
        }
