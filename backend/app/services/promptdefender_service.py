from sqlalchemy.orm import Session
from ..models.promptdefender import PromptInjectionLog, HallucinationAnalysis, SyntheticContentForensics, CrossModuleLink
from ..schemas.promptdefender import PromptInjectionRequest, HallucinationRequest, SyntheticForensicsRequest, CrossModuleLinkRequest
from ..modules.promptdefender_engine import InjectionDetector, HallucinationAnalyzer, SyntheticForensics, LinkageEngine

class PromptDefenderService:
    @staticmethod
    def detect_injection(db: Session, payload: PromptInjectionRequest) -> dict:
        result = InjectionDetector.detect(payload.prompt)
        
        log = PromptInjectionLog(
            session_id=payload.session_id,
            original_prompt=payload.prompt,
            is_injection=result["is_injection"],
            threat_score=result["threat_score"],
            sanitized_prompt=result["sanitized_prompt"]
        )
        db.add(log)
        db.commit()
        
        return {
            "session_id": payload.session_id,
            "is_injection": result["is_injection"],
            "threat_score": result["threat_score"],
            "sanitized_prompt": result["sanitized_prompt"]
        }

    @staticmethod
    def analyze_hallucination(db: Session, payload: HallucinationRequest) -> dict:
        result = HallucinationAnalyzer.analyze(payload.generated_text, payload.factual_baseline)
        
        analysis = HallucinationAnalysis(
            generated_text=payload.generated_text,
            factual_consistency_score=result["factual_consistency_score"],
            is_hallucination=result["is_hallucination"],
            flag_reason=result["flag_reason"]
        )
        db.add(analysis)
        db.commit()
        
        return result

    @staticmethod
    def analyze_synthetic(db: Session, payload: SyntheticForensicsRequest) -> dict:
        result = SyntheticForensics.analyze(payload.text_sample)
        
        forensics = SyntheticContentForensics(
            text_sample=payload.text_sample,
            perplexity_score=result["perplexity_score"],
            burstiness_score=result["burstiness_score"],
            is_ai_generated=result["is_ai_generated"]
        )
        db.add(forensics)
        db.commit()
        
        return result

    @staticmethod
    def link_module(db: Session, payload: CrossModuleLinkRequest) -> dict:
        result = LinkageEngine.link(payload.source_event_id, payload.target_module)
        
        link = CrossModuleLink(
            source_event_id=payload.source_event_id,
            target_module=payload.target_module
        )
        db.add(link)
        db.commit()
        
        return result
