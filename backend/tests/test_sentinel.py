import pytest
from backend.app.services.sentinel_core import SentinelCore
from backend.app.services.sentinel_agents import (
    OrchestratorAgent,
    IntelligenceAgent,
    ForensicsAgent,
    ActionAgent,
)

@pytest.fixture
def sentinel():
    return SentinelCore()

def test_sentinel_initialization(sentinel):
    assert sentinel.VERSION == "2.0.0"
    assert sentinel.CODENAME == "SENTINEL-AEGIS"
    assert isinstance(sentinel.agents["orchestrator"], OrchestratorAgent)
    assert isinstance(sentinel.agents["intelligence"], IntelligenceAgent)
    assert isinstance(sentinel.agents["forensics"], ForensicsAgent)
    assert isinstance(sentinel.agents["action"], ActionAgent)

def test_intent_classification(sentinel):
    # Test Malware Intent
    intent, conf, kws = sentinel._classify_intent("We found a new ransomware executable payload")
    assert intent == "malware"
    assert conf > 0.0

    # Test Deepfake Intent
    intent, conf, kws = sentinel._classify_intent("Check this manipulated video for face swap deepfake")
    assert intent == "deepfake"
    
    # Test Phishing
    intent, conf, kws = sentinel._classify_intent("User reported a spear phishing email credential attack")
    assert intent == "phishing"

def test_process_message_general(sentinel):
    result = sentinel.process_message("Hello Sentinel, give me a status update")
    assert result["request_id"] is not None
    assert result["intent"] == "general"
    assert "status" in result["reply"].lower() or "nominal" in result["reply"].lower()
    assert result["agent_used"] == "orchestrator"
    assert len(result["xai_trace"]["chain_of_thought"]) > 0

def test_process_message_malware(sentinel):
    result = sentinel.process_message("Analyze this suspicious ransomware payload we found on the server.")
    assert result["intent"] == "malware"
    assert result["agent_used"] == "forensics"
    assert result["module_invoked"] == "malware"
    assert result["threat_score"] > 0.5  # Malware has high severity boost
    
def test_guardrails_pii(sentinel):
    result = sentinel.process_message("Here is the attacker email: badguy@hacker.com and aadhaar 1234 5678 9012")
    assert "badguy@hacker.com" not in result["reply"]
    assert "1234 5678 9012" not in result["reply"]
    # Check if flags were raised (depending on if the agent echoed it, which it might not, 
    # but the guardrail engine itself can be tested)
    filtered, flags = sentinel.guardrails.filter_output("User email is test@realuser.com")
    assert "REDACTED" in filtered
    assert len(flags) > 0
    assert flags[0]["type"] == "PII_REDACTED"

def test_guardrails_restricted_action(sentinel):
    filtered, flags = sentinel.guardrails.filter_output("I will now execute rm -rf on the server")
    assert len(flags) > 0
    assert flags[0]["type"] == "RESTRICTED_ACTION_DETECTED"

def test_memory_storage_and_retrieval(sentinel):
    # Store an interaction
    sentinel.memory.store_interaction(
        query="What is the IP of the C2 server?",
        response="The C2 server is located at 192.168.1.100",
        intent="malware",
        threat_score=0.9,
        user_id="test_user"
    )
    
    # Retrieve it
    context = sentinel.memory.retrieve_context("What is the C2 IP?", top_k=1)
    assert len(context) > 0
    assert "192.168.1.100" in context[0]["response"]
