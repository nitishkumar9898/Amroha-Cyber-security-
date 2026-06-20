import React, { useState } from 'react';
import './HumanForgeDashboard.css';

interface PhishingResult {
  message_id: string;
  is_phishing: boolean;
  confidence_score: number;
  detected_markers: string;
}

interface ManipulationResult {
  transcript_id: string;
  manipulation_type: string;
  severity_level: string;
}

interface SimulationResult {
  employee_id: string;
  scenario_type: string;
  payload_content: string;
  difficulty_rating: number;
}

interface InsiderLinkResult {
  employee_id: string;
  base_insider_risk: number;
  adjusted_insider_risk: number;
  reasoning: string;
}

export default function HumanForgeDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Phishing State
  const [msgId, setMsgId] = useState('MSG-001');
  const [contentBody, setContentBody] = useState('Urgent action required: Reset your password immediately via this wire transfer link.');
  const [senderDomain, setSenderDomain] = useState('admin-support.co');
  const [phishingResult, setPhishingResult] = useState<PhishingResult | null>(null);

  // Manipulation State
  const [transcriptId, setTranscriptId] = useState('TRANS-XYZ');
  const [urgencyLevel, setUrgencyLevel] = useState<number>(9.5);
  const [authImpersonation, setAuthImpersonation] = useState<boolean>(true);
  const [manipulationResult, setManipulationResult] = useState<ManipulationResult | null>(null);

  // Simulation State
  const [employeeIdSim, setEmployeeIdSim] = useState('EMP-505');
  const [targetVuln, setTargetVuln] = useState('FINANCIAL_URGENCY');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);

  // Insider Link State
  const [employeeIdLink, setEmployeeIdLink] = useState('EMP-505');
  const [baseRisk, setBaseRisk] = useState<number>(50.0);
  const [failedSims, setFailedSims] = useState<number>(3);
  const [insiderResult, setInsiderResult] = useState<InsiderLinkResult | null>(null);

  const handleDetectPhishing = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPhishingResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/humanforge/detect-phishing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: msgId,
          content_body: contentBody,
          sender_domain: senderDomain
        })
      });
      if (!response.ok) throw new Error('Phishing detection failed');
      setPhishingResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeManipulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setManipulationResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/humanforge/analyze-manipulation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript_id: transcriptId,
          urgency_level: urgencyLevel,
          authority_impersonation: authImpersonation
        })
      });
      if (!response.ok) throw new Error('Manipulation analysis failed');
      setManipulationResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateAwareness = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSimulationResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/humanforge/simulate-awareness', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeIdSim,
          target_vulnerability: targetVuln
        })
      });
      if (!response.ok) throw new Error('Simulation generation failed');
      setSimulationResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkInsider = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setInsiderResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/humanforge/link-insider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeIdLink,
          base_insider_risk: baseRisk,
          failed_simulations_count: failedSims
        })
      });
      if (!response.ok) throw new Error('Insider linking failed');
      setInsiderResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="humanforge-dashboard">
      <header className="hf-header">
        <h1>🧠 HumanForge Architect</h1>
        <p>Cyber Psychology, Social Engineering Defense, & Behavioral Profiling</p>
      </header>

      {error && <div className="hf-alert">{error}</div>}

      <div className="hf-grid">
        {/* Left Column */}
        <div>
          <div className="hf-panel" style={{ marginBottom: '2rem' }}>
            <h2>🎣 Advanced Phishing Detection</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Scan incoming text for sophisticated vishing/phishing NLP markers and spoofed domains.
            </p>
            <form onSubmit={handleDetectPhishing}>
              <div className="hf-form-group">
                <label>Message/Transcript ID</label>
                <input type="text" value={msgId} onChange={(e) => setMsgId(e.target.value)} required />
              </div>
              <div className="hf-form-group">
                <label>Sender Domain</label>
                <input type="text" value={senderDomain} onChange={(e) => setSenderDomain(e.target.value)} required />
              </div>
              <div className="hf-form-group">
                <label>Content Body</label>
                <textarea rows={3} value={contentBody} onChange={(e) => setContentBody(e.target.value)} required />
              </div>
              <button type="submit" className="hf-btn" disabled={loading}>Scan Content</button>
            </form>

            {phishingResult && (
              <div className={`hf-result-box ${phishingResult.is_phishing ? 'danger' : 'nominal'}`}>
                <div className="hf-result-title" style={{ color: phishingResult.is_phishing ? '#ff4444' : '#00ffcc' }}>
                  {phishingResult.is_phishing ? 'PHISHING DETECTED' : 'CONTENT SAFE'}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  <strong>Confidence: </strong> {phishingResult.confidence_score.toFixed(1)}%
                </div>
                <div style={{ color: '#888', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                  {phishingResult.detected_markers}
                </div>
              </div>
            )}
          </div>

          <div className="hf-panel">
            <h2>🎭 Psychological Manipulation Analysis</h2>
            <form onSubmit={handleAnalyzeManipulation}>
              <div className="hf-form-group">
                <label>Transcript ID</label>
                <input type="text" value={transcriptId} onChange={(e) => setTranscriptId(e.target.value)} required />
              </div>
              <div className="hf-form-group">
                <label>Detected Urgency Level (0-10)</label>
                <input type="number" step="0.1" value={urgencyLevel} onChange={(e) => setUrgencyLevel(parseFloat(e.target.value))} required />
              </div>
              <div className="hf-form-group" style={{ display: 'flex', alignItems: 'center', marginTop: '1.5rem', marginBottom: '1.5rem' }}>
                <input type="checkbox" id="authCheck" checked={authImpersonation} onChange={(e) => setAuthImpersonation(e.target.checked)} />
                <label htmlFor="authCheck" style={{ margin: 0, color: '#e0e0e0' }}>Authority Impersonation Detected (e.g. CEO, IT)</label>
              </div>
              <button type="submit" className="hf-btn" disabled={loading} style={{ background: '#b721ff', color: '#fff' }}>Analyze Cognitive Bias</button>
            </form>

            {manipulationResult && (
              <div className={`hf-result-box ${manipulationResult.severity_level === 'CRITICAL' ? 'danger' : 'warning'}`}>
                <div className="hf-result-title" style={{ color: manipulationResult.severity_level === 'CRITICAL' ? '#ff4444' : '#fca311' }}>
                  SEVERITY: {manipulationResult.severity_level}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  {manipulationResult.manipulation_type}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="hf-panel" style={{ marginBottom: '2rem' }}>
            <h2>🎯 Awareness Training Simulator</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Generate highly targeted mock-phishing payloads based on known employee psychological vulnerabilities.
            </p>
            <form onSubmit={handleSimulateAwareness}>
              <div className="hf-form-group">
                <label>Employee ID</label>
                <input type="text" value={employeeIdSim} onChange={(e) => setEmployeeIdSim(e.target.value)} required />
              </div>
              <div className="hf-form-group">
                <label>Target Vulnerability Vector</label>
                <select value={targetVuln} onChange={(e) => setTargetVuln(e.target.value)}>
                  <option value="FINANCIAL_URGENCY">Financial Urgency (Payroll/Bonus)</option>
                  <option value="IT_SUPPORT_SPOOF">IT Support Spoof (Mandatory Update)</option>
                  <option value="GENERIC">Generic Newsletter</option>
                </select>
              </div>
              <button type="submit" className="hf-btn" disabled={loading} style={{ background: '#00ffcc', color: '#000' }}>Generate Payload</button>
            </form>

            {simulationResult && (
              <div className="hf-result-box nominal">
                <div className="hf-result-title" style={{ color: '#00ffcc' }}>✓ Payload Generated</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Mock Content</div>
                    <div style={{ color: '#e0e0e0', fontStyle: 'italic', background: '#222', padding: '0.5rem', borderRadius: '4px', marginTop: '0.25rem' }}>
                      "{simulationResult.payload_content}"
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Difficulty Rating</div>
                    <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{simulationResult.difficulty_rating.toFixed(1)} / 10</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="hf-panel">
            <h2>🔗 Insider Threat Integration</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Elevate Insider Risk scores automatically based on repeated susceptibility to psychological profiling.
            </p>
            <form onSubmit={handleLinkInsider}>
              <div className="hf-form-group">
                <label>Employee ID</label>
                <input type="text" value={employeeIdLink} onChange={(e) => setEmployeeIdLink(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="hf-form-group">
                  <label>Base Insider Risk</label>
                  <input type="number" step="0.1" value={baseRisk} onChange={(e) => setBaseRisk(parseFloat(e.target.value))} required />
                </div>
                <div className="hf-form-group">
                  <label>Failed Simulations</label>
                  <input type="number" value={failedSims} onChange={(e) => setFailedSims(parseInt(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="hf-btn" disabled={loading} style={{ background: '#ffaa00', color: '#000' }}>Recalculate Risk Score</button>
            </form>

            {insiderResult && (
              <div className={`hf-result-box ${insiderResult.adjusted_insider_risk > 75 ? 'danger' : 'warning'}`}>
                <div className="hf-result-title" style={{ color: insiderResult.adjusted_insider_risk > 75 ? '#ff4444' : '#ffaa00' }}>
                  NEW RISK SCORE: {insiderResult.adjusted_insider_risk.toFixed(1)}
                </div>
                <div style={{ color: '#888', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                  {insiderResult.reasoning}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
