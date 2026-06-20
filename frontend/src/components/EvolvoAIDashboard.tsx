import React, { useState } from 'react';
import { submitFeedback, checkDrift, triggerRetraining } from '../api/evolvoai';
import './EvolvoAIDashboard.css';

const EvolvoAIDashboard: React.FC = () => {
  const [dataId, setDataId] = useState('');
  const [label, setLabel] = useState('');
  const [status, setStatus] = useState('');
  const [driftResult, setDriftResult] = useState<any>(null);

  const handleFeedback = async () => {
    setStatus('Submitting HITL feedback...');
    await submitFeedback(dataId, label, 'Analyst_A1');
    setStatus('Feedback submitted successfully. Queued for dataset curation.');
    setDataId('');
    setLabel('');
  };

  const handleCheckDrift = async () => {
    setStatus('Checking model drift...');
    const res = await checkDrift('threat_model_v1', 0.82); // simulating a drop in accuracy
    setDriftResult(res);
    setStatus('Drift check complete.');
  };

  const handleRetrain = async () => {
    setStatus('Triggering continual learning pipeline...');
    await triggerRetraining('threat_model_v1', 'ds_curated_latest');
    setStatus('Retraining pipeline triggered. Check model registry for updates.');
  };

  return (
    <div className="ev-dashboard-container">
      <h1 className="ev-title">EvolvoAI Continuous Learning</h1>

      {status && <div className="ev-status">{status}</div>}

      <div className="ev-grid">
        <div className="ev-card">
          <h2>Human-in-the-Loop (HITL)</h2>
          <p>Correct false positives/negatives to improve future models.</p>
          <div className="ev-form">
            <input 
              type="text" 
              placeholder="Data/Event ID" 
              value={dataId} 
              onChange={(e) => setDataId(e.target.value)} 
              className="ev-input"
            />
            <input 
              type="text" 
              placeholder="Corrected Label (e.g., Benign)" 
              value={label} 
              onChange={(e) => setLabel(e.target.value)} 
              className="ev-input"
            />
            <button className="ev-btn" onClick={handleFeedback}>Submit Correction</button>
          </div>
        </div>

        <div className="ev-card">
          <h2>Performance Monitor</h2>
          <button className="ev-btn ev-btn-alt" onClick={handleCheckDrift}>Check Model Drift</button>
          
          {driftResult && (
            <div className="ev-drift-results">
              <p><strong>Model:</strong> {driftResult.model_id}</p>
              <p><strong>Recent Accuracy:</strong> {(driftResult.recent_accuracy * 100).toFixed(1)}%</p>
              <p><strong>Drift Detected:</strong> {driftResult.drift_detected ? 'Yes ⚠️' : 'No ✅'}</p>
              
              {driftResult.drift_detected && (
                <button className="ev-btn ev-btn-danger" onClick={handleRetrain}>
                  Trigger Retraining Pipeline
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EvolvoAIDashboard;
