import React, { useState } from 'react';
import './EthicsForgeDashboard.css';

interface Policy {
  policy_name: string;
  description: string;
  severity_level: string;
}

interface ActionEvalResult {
  decision: string;
  justification: string;
}

interface BiasScanResult {
  model_name: string;
  bias_score: number;
  demographic_skew_detected: boolean;
  mitigation_applied: boolean;
}

export default function EthicsForgeDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [policies, setPolicies] = useState<Policy[]>([]);
  
  // Policy Form State
  const [policyName, setPolicyName] = useState('');
  const [policyDesc, setPolicyDesc] = useState('');
  const [severity, setSeverity] = useState('CRITICAL');

  // Eval Form State
  const [moduleSource, setModuleSource] = useState('ResponseForge');
  const [proposedAction, setProposedAction] = useState('AUTOMATED_ISOLATION');
  const [actionContext, setActionContext] = useState('DDoS signature detected on edge router.');
  const [evalResult, setEvalResult] = useState<ActionEvalResult | null>(null);
  const [xaiReport, setXaiReport] = useState<string | null>(null);

  // Bias Scan State
  const [modelName, setModelName] = useState('InsiderRisk_v2');
  const [datasetSignature, setDatasetSignature] = useState('HR_DATA_WITH_DEMO_SKEW');
  const [biasResult, setBiasResult] = useState<BiasScanResult | null>(null);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/ethicsforge/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          policy_name: policyName,
          description: policyDesc,
          severity_level: severity
        })
      });
      if (!response.ok) throw new Error('Failed to create policy');
      const newPolicy = await response.json();
      setPolicies([...policies, newPolicy]);
      setPolicyName('');
      setPolicyDesc('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setEvalResult(null);
    setXaiReport(null);
    try {
      const response = await fetch('http://localhost:8000/api/ethicsforge/evaluate-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          module_source: moduleSource,
          proposed_action: proposedAction,
          action_context: actionContext
        })
      });
      if (!response.ok) throw new Error('Failed to evaluate action');
      const data = await response.json();
      setEvalResult(data);
      
      // Auto-fetch XAI transparency report (mocking log_id=1 for demo since DB resets)
      const xaiResponse = await fetch('http://localhost:8000/api/ethicsforge/transparency-report/1');
      if (xaiResponse.ok) {
        const xaiData = await xaiResponse.json();
        setXaiReport(xaiData.xai_explanation);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScanBias = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setBiasResult(null);
    try {
      const response = await fetch('http://localhost:8000/api/ethicsforge/scan-bias', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_name: modelName,
          dataset_signature: datasetSignature
        })
      });
      if (!response.ok) throw new Error('Failed to run bias scan');
      setBiasResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ethicsforge-dashboard">
      <header className="ef-header">
        <h1>⚖️ EthicsForge Architect</h1>
        <p>AI Governance, Bias Detection, and Transparency Reporting</p>
      </header>

      {error && <div className="ef-alert">{error}</div>}

      <div className="ef-grid">
        {/* Left Column: Policy Management & Bias Scanning */}
        <div>
          <div className="ef-panel" style={{ marginBottom: '2rem' }}>
            <h2>📜 Define Governance Policy</h2>
            <form onSubmit={handleCreatePolicy}>
              <div className="ef-form-group">
                <label>Policy Name</label>
                <input type="text" value={policyName} onChange={(e) => setPolicyName(e.target.value)} required placeholder="e.g., HITL Requirement" />
              </div>
              <div className="ef-form-group">
                <label>Description (Keywords match actions)</label>
                <textarea value={policyDesc} onChange={(e) => setPolicyDesc(e.target.value)} required placeholder="e.g., All LETHAL or AUTOMATED_ISOLATION actions require Human-in-the-loop review." rows={3}></textarea>
              </div>
              <div className="ef-form-group">
                <label>Severity Level</label>
                <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                  <option value="CRITICAL">CRITICAL (Hard Blocker - Vetoes Action)</option>
                  <option value="WARNING">WARNING (Soft Advisory - Flags Action)</option>
                </select>
              </div>
              <button type="submit" className="ef-btn" disabled={loading}>Establish Policy</button>
            </form>
          </div>

          {policies.length > 0 && (
            <div className="ef-panel" style={{ marginBottom: '2rem' }}>
              <h2>✅ Active Policies</h2>
              {policies.map((p, idx) => (
                <div key={idx} className={`ef-policy-card ${p.severity_level.toLowerCase()}`}>
                  <span className={`ef-policy-badge ${p.severity_level.toLowerCase()}`}>{p.severity_level}</span>
                  <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>{p.policy_name}</div>
                  <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{p.description}</div>
                </div>
              ))}
            </div>
          )}

          <div className="ef-panel">
            <h2>🔍 AI Model Bias Scanner</h2>
            <form onSubmit={handleScanBias}>
              <div className="ef-form-group">
                <label>Target Model</label>
                <input type="text" value={modelName} onChange={(e) => setModelName(e.target.value)} required />
              </div>
              <div className="ef-form-group">
                <label>Dataset Signature</label>
                <input type="text" value={datasetSignature} onChange={(e) => setDatasetSignature(e.target.value)} required />
              </div>
              <button type="submit" className="ef-btn" disabled={loading} style={{ background: '#333', color: '#fff' }}>Run Statistical Bias Scan</button>
            </form>

            {biasResult && (
              <div style={{ marginTop: '1.5rem', textAlign: 'center', padding: '1rem', background: '#111', borderRadius: '4px' }}>
                <div style={{ color: '#888', marginBottom: '0.5rem' }}>Bias Score (Lower is better)</div>
                <div className={`ef-bias-score ${biasResult.bias_score > 0.5 ? 'high' : 'low'}`}>
                  {biasResult.bias_score.toFixed(2)}
                </div>
                {biasResult.demographic_skew_detected ? (
                  <div style={{ color: '#ff4444', fontWeight: 'bold', marginBottom: '0.5rem' }}>⚠️ Demographic Skew Detected!</div>
                ) : (
                  <div style={{ color: '#00ff88', fontWeight: 'bold', marginBottom: '0.5rem' }}>✅ Model Weights Balanced</div>
                )}
                {biasResult.mitigation_applied && (
                  <div style={{ color: '#00ccff', fontSize: '0.9rem' }}>Auto-mitigation logic applied to model output layer.</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Ethical Arbiter Sandbox */}
        <div>
          <div className="ef-panel">
            <h2>⚖️ Ethical Arbiter Sandbox</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Simulate submitting an automated action from another platform module to the EthicsForge Arbiter for review against active policies.
            </p>
            <form onSubmit={handleEvaluateAction}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="ef-form-group">
                  <label>Requesting Module</label>
                  <input type="text" value={moduleSource} onChange={(e) => setModuleSource(e.target.value)} required />
                </div>
                <div className="ef-form-group">
                  <label>Proposed Action</label>
                  <input type="text" value={proposedAction} onChange={(e) => setProposedAction(e.target.value)} required />
                </div>
              </div>
              <div className="ef-form-group">
                <label>Action Context (Why is the AI proposing this?)</label>
                <textarea value={actionContext} onChange={(e) => setActionContext(e.target.value)} required rows={2}></textarea>
              </div>
              <button type="submit" className="ef-btn" disabled={loading}>Submit for Ethical Evaluation</button>
            </form>

            {evalResult && (
              <div className="ef-audit-log" style={{ marginTop: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', paddingBottom: '0.5rem' }}>
                  <span style={{ color: '#888' }}>Arbiter Decision:</span>
                  <span className={`ef-decision ${evalResult.decision.toLowerCase()}`}>{evalResult.decision}</span>
                </div>
                <div style={{ marginTop: '0.5rem' }}>
                  <strong style={{ color: '#aaa' }}>Arbiter Justification:</strong><br/>
                  {evalResult.justification}
                </div>

                {xaiReport && (
                  <div style={{ marginTop: '1rem' }}>
                    <strong style={{ color: '#00ccff' }}>XAI Transparency Report:</strong>
                    <div className="ef-xai-box">{xaiReport}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
