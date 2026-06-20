"""
DeepGuard AI Unified Orchestrator Service
Integrates deepfake classifiers, network cascade trackers, and psychological profilers
into a single multimodal detection engine with full Explainable AI output.
"""
import time
from typing import Dict, Any, List
from ..modules.deepfake import DeepfakeDetector
from ..modules.misinfo_propagation import MisinfoPropagationTracker
from ..modules.psychology import CyberPsychologyProfiler

class DeepGuardService:
    def __init__(self):
        self.version = "1.0.0"
        self.name = "DeepGuard-Consensus-Core"
        
    def evaluate_incident(self, media_path: str, context_text: str) -> Dict[str, Any]:
        """
        Coordinates evaluation of an incident using multimodal checks.
        Combines audio-visual forensics with propagation dynamics and linguistic psychology.
        """
        start_time = time.time()
        
        # 1. Audios / Video / Image Deepfake Analysis
        forensics = DeepfakeDetector.analyze_media(media_path)
        
        # 2. Linguistic Psychology & Intent Profiling
        psychology = CyberPsychologyProfiler.profile_incident_text(context_text)
        
        # 3. Misinformation Propagation Analytics
        propagation = MisinfoPropagationTracker.analyze_propagation(context_text)
        
        # Multimodal Consensus Scoring (weighted aggregator)
        auth_score = forensics["authenticity_score"]
        threat_score = psychology["linguistic_metrics"]["threat_score"]
        bot_ratio = propagation["metrics"]["bot_influence_ratio"]
        
        # Global credibility score: lower means more likely fake/coordinated
        global_credibility = round((auth_score * 0.4) + ((1 - threat_score) * 0.3) + ((1 - bot_ratio) * 0.3), 2)
        
        verdict = "HIGH_RISK_INFLUENCE_CAMPAIGN"
        if global_credibility > 0.70:
            verdict = "VERIFIED_AUTHENTIC"
        elif global_credibility > 0.40:
            verdict = "SUSPICIOUS_UNVERIFIED_CONTENT"
            
        # Explanations
        xai_traces = []
        xai_traces.extend(forensics["explainability_traces"])
        
        for strategy in psychology["cognitive_profile"]["manipulation_strategies_deployed"]:
            xai_traces.append(f"Psychological exploitation strategy: {strategy}.")
            
        if bot_ratio > 0.35:
            xai_traces.append(f"Network propagation: High bot-to-human ratio ({int(bot_ratio*100)}%) matches synthetic amplifications.")

        processing_ms = int((time.time() - start_time) * 1000)
        
        return {
            "deepguard_version": self.version,
            "incident_verdict": verdict,
            "credibility_index": global_credibility,
            "processing_time_ms": processing_ms,
            "components": {
                "forensic_analysis": forensics,
                "psychological_profile": psychology,
                "propagation_cascade": propagation
            },
            "explainability_report": {
                "decision_rationales": xai_traces,
                "modality_weights": {
                    "media_forensics_weight": 0.4,
                    "psychology_weight": 0.3,
                    "propagation_weight": 0.3
                }
            }
        }

deepguard_engine = DeepGuardService()
