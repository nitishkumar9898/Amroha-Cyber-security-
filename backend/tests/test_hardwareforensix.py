import pytest
from app.modules.hardwareforensix.image_analyzer import image_analyzer
from app.modules.hardwareforensix.side_channel_detector import side_channel_detector
from app.modules.hardwareforensix.firmware_re import firmware_re
from app.modules.hardwareforensix.hardware_sandbox import hardware_sandbox
from app.modules.hardwareforensix.cross_module_bridge import cross_module_bridge

@pytest.mark.asyncio
async def test_image_analyzer():
    dummy_data = b"0123456789ABCDEF"
    analysis = await image_analyzer.analyze_firmware_image(dummy_data)
    assert analysis["size_bytes"] == 16
    assert "sha256" in analysis
    assert "entropy" in analysis

@pytest.mark.asyncio
async def test_side_channel_detector():
    normal_trace = [0.1, 0.2, 0.15, 0.1]
    res_normal = await side_channel_detector.detect_anomalies(normal_trace, "power")
    assert not res_normal["attack_detected"]
    
    attack_trace = [0.95] * 150
    res_attack = await side_channel_detector.detect_anomalies(attack_trace, "power")
    assert res_attack["attack_detected"]

@pytest.mark.asyncio
async def test_firmware_re():
    code = "char buffer[10]; strcpy(buffer, input);"
    res = await firmware_re.analyze_code_snippet(code, "ARM")
    assert any(v["type"] == "Buffer Overflow" for v in res["vulnerabilities"])

@pytest.mark.asyncio
async def test_hardware_sandbox():
    res = await hardware_sandbox.execute_firmware("fw-123", "ARM")
    assert res["firmware_id"] == "fw-123"
    assert "network_activity" in res

@pytest.mark.asyncio
async def test_cross_module_bridge():
    data = {"findings": ["High entropy", "Packed"]}
    res = await cross_module_bridge.correlate_findings(data)
    assert res["correlation_score"] > 0.5
    assert res["action_required"]
