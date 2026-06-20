import pytest
from app.modules.evolvoai.continual_learner import continual_learner
from app.modules.evolvoai.dataset_curator import dataset_curator
from app.modules.evolvoai.performance_monitor import performance_monitor
from app.modules.evolvoai.model_registry import model_registry
from app.modules.evolvoai.hitl_feedback import hitl_feedback

@pytest.mark.asyncio
async def test_continual_learner():
    res = await continual_learner.train_incremental("model_1", "ds_1")
    assert res["status"] == "completed"
    assert "metrics" in res

@pytest.mark.asyncio
async def test_dataset_curator():
    data = [{"confidence": 0.95}, {"confidence": 0.8}]
    res = await dataset_curator.curate_from_modules(data)
    assert res["curated_count"] == 1

@pytest.mark.asyncio
async def test_performance_monitor():
    res_drift = await performance_monitor.check_drift("model_1", 0.8)
    assert res_drift["drift_detected"]
    
    res_ok = await performance_monitor.check_drift("model_1", 0.9)
    assert not res_ok["drift_detected"]

@pytest.mark.asyncio
async def test_model_registry():
    await model_registry.register_model("model_2", "v1", {"acc": 0.9})
    assert "model_2" in model_registry.models
    assert len(model_registry.models["model_2"]) == 1
    
    success = await model_registry.promote_model("model_2", "v1")
    assert success
    assert model_registry.models["model_2"][0]["status"] == "production"

@pytest.mark.asyncio
async def test_hitl_feedback():
    res = await hitl_feedback.submit_feedback("data_1", "malicious", "analyst_john")
    assert res["data_id"] == "data_1"
    assert hitl_feedback.feedback_queue[0]["status"] == "pending_curation"
