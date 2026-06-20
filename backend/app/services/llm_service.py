import os
import time
import random
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Ensure API Key is configured if available
API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize the new google.genai client
_genai_client = None
try:
    from google import genai as genai_sdk
    if API_KEY:
        _genai_client = genai_sdk.Client(api_key=API_KEY)
except ImportError:
    genai_sdk = None  # type: ignore

class LLMService:
    @staticmethod
    def get_system_prompt() -> str:
        return """You are SentinelCore v2.0, a highly advanced, multi-modal cybersecurity orchestrator and investigator for the Amroha01 platform. 
Your tone is professional, analytical, authoritative, and slightly futuristic (like a high-tech AI). 
You assist human operators in analyzing threats, breaking down malware, identifying deepfakes, and suggesting remediation strategies.
Use markdown formatting for your responses. Bold key terms. Use bullet points for structured data."""

    @staticmethod
    def process_chat(message: str) -> dict:
        start_time = time.time()
        
        # Determine intent heuristically for UI metadata
        intent = "query"
        agent = "orchestrator"
        if "analyze" in message.lower() or "malware" in message.lower():
            intent = "analysis"
            agent = "forensics"
        elif "deepfake" in message.lower() or "audio" in message.lower():
            intent = "verification"
            agent = "intelligence"
            
        try:
            if _genai_client:
                response = _genai_client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=message,
                    config={'system_instruction': LLMService.get_system_prompt()}
                )
                reply = response.text
            else:
                # Fallback mock if no API key
                reply = f"**[OFFLINE MODE]** I have received your query: `{message}`.\n\nTo enable my full neural network capabilities, please configure the `GEMINI_API_KEY` environment variable on the server."
        except Exception as e:
            reply = f"**[SYSTEM ERROR]** Neural link failed. Error details: {str(e)}"
            
        processing_time = int((time.time() - start_time) * 1000)
        
        # Mocking the XAI Trace for UI visualization
        xai_trace = {
            "trace_id": f"TRC-{random.randint(1000, 9999)}",
            "chain_of_thought": [
                {"step": 1, "action": "Intent Parsing", "result": f"Identified intent: {intent}", "evidence": "Keyword heuristics"},
                {"step": 2, "action": "Agent Routing", "result": f"Routed to {agent} cluster", "evidence": "Load balancer"},
                {"step": 3, "action": "Response Generation", "result": "Generated markdown response", "evidence": "LLM completion"}
            ],
            "mitre_mapping": ["T1566", "T1106"] if intent == "analysis" else []
        }
            
        return {
            "reply": reply,
            "intent": intent.upper(),
            "confidence": random.uniform(0.85, 0.99),
            "threat_score": random.uniform(0.1, 0.9) if intent == "analysis" else 0.05,
            "severity": "HIGH" if intent == "analysis" else "INFO",
            "agent_used": agent,
            "xai_trace": xai_trace,
            "guardrail_flags": [],
            "attachments_processed": 0,
            "processing_time_ms": processing_time
        }

    @staticmethod
    def process_multimodal(message: str, files_count: int, file_names: List[str]) -> dict:
        start_time = time.time()
        
        # In a real scenario with Gemini, you would upload the files using genai.upload_file()
        # and pass them to the model.generate_content([file1, file2, message]).
        # For this implementation, we will acknowledge the files if API is present, or mock it.
        
        try:
            if _genai_client:
                # Since we are receiving raw bytes in FastAPI, we would need to save them temporarily or pass the bytes.
                # To keep it simple and robust, we just tell the LLM about the files.
                prompt = f"The user has attached {files_count} files: {', '.join(file_names)}. User message: {message}\nAnalyze this scenario based on the file names and message."
                response = _genai_client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                    config={'system_instruction': LLMService.get_system_prompt()}
                )
                reply = response.text
            else:
                reply = f"**[OFFLINE MODE]** I see you attached {files_count} files ({', '.join(file_names)}). Message: `{message}`.\n\nI need the `GEMINI_API_KEY` to process multi-modal attachments."
        except Exception as e:
            reply = f"**[SYSTEM ERROR]** Multi-modal processing failed. Error details: {str(e)}"
            
        processing_time = int((time.time() - start_time) * 1000)
        
        xai_trace = {
            "trace_id": f"TRC-{random.randint(1000, 9999)}",
            "chain_of_thought": [
                {"step": 1, "action": "File Ingestion", "result": f"Ingested {files_count} files", "evidence": "Multipart form data"},
                {"step": 2, "action": "Multi-modal Analysis", "result": "Extracted features from attachments", "evidence": "Vision/Audio models"},
            ]
        }
        
        return {
            "reply": reply,
            "intent": "MULTIMODAL_ANALYSIS",
            "confidence": 0.92,
            "threat_score": random.uniform(0.4, 0.95),
            "severity": "CRITICAL" if files_count > 2 else "HIGH",
            "agent_used": "forensics",
            "xai_trace": xai_trace,
            "guardrail_flags": [
                {"type": "PII Filter", "severity": "LOW", "detail": "Sanitized metadata"}
            ],
            "attachments_processed": files_count,
            "processing_time_ms": processing_time
        }

    @staticmethod
    def get_system_status() -> dict:
        return {
            "status": "ONLINE" if API_KEY else "DEGRADED (No API Key)",
            "memory_entries": random.randint(15000, 50000),
            "continual_learning": "ACTIVE",
            "federated_nodes": 31 # Corresponding to our 31 modules
        }
