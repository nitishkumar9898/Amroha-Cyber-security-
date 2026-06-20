from pydantic import BaseModel, ConfigDict
from typing import Optional

class PromptInjectionRequest(BaseModel):
    session_id: str
    prompt: str

class PromptInjectionResult(BaseModel):
    session_id: str
    is_injection: bool
    threat_score: float
    sanitized_prompt: str

class HallucinationRequest(BaseModel):
    generated_text: str
    factual_baseline: str

class HallucinationResult(BaseModel):
    factual_consistency_score: float
    is_hallucination: bool
    flag_reason: str

class SyntheticForensicsRequest(BaseModel):
    text_sample: str

class SyntheticForensicsResult(BaseModel):
    perplexity_score: float
    burstiness_score: float
    is_ai_generated: bool
    confidence: float

class CrossModuleLinkRequest(BaseModel):
    source_event_id: str
    target_module: str

class CrossModuleLinkResult(BaseModel):
    status: str
    source_event_id: str
    target_module: str
