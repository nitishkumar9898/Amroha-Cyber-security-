import React, { useState } from 'react';
import './NeuroGuardDashboard.css';

interface NeuralScanResult {
  subject_id: string;
  is_anomalous: boolean;
  anomaly_type: string | null;
  status_message: string;
}

interface BCISimResult {
  attack_vector: string;
  biological_impact: string;
  countermeasure_deployed: string;
}

interface PrivacyResult {
  data_packet_id: string;
  is_secure: boolean;
  encryption_standard: string;
  message: string;
}

export default function NeuroGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scan State
  const [subjectId, setSubjectId] = useState('OP-774');
  const [alpha, setAlpha] = useState<number>(10.5);
  const [beta, setBeta] = useState<number>(20.0);
  const [gamma, setGamma] = useState<number>(40.0);
  const [scanResult, setScanResult] = useState<NeuralScanResult | null>(null);

  // Sim State
  const [attackVector, setAttackVector] = useState('MEMORY_ALTERATION');
  const [simResult, setSimResult] = useState<BCISimResult | null>(null);

  // Privacy State
  const [packetId, setPacketId] = useState('PKT-112233');
  const [thoughtData, setThoughtData] = useState('RAW_VISUAL_CORTEX_STREAM');
  const [privacyResult, setPrivacyResult] = useState<PrivacyResult | null>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setScanResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/neuroguard/analyze-telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject_id: subjectId,
          alpha_band_hz: alpha,
          beta_band_hz: beta,
          gamma_band_hz: gamma
        })
      });
      if (!response.ok) throw new Error('Scan failed');
      setScanResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSimResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/neuroguard/simulate-bci-hack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attack_vector: attackVector })
      });
      if (!response.ok) throw new Error('Simulation failed');
      setSimResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePrivacy = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPrivacyResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/neuroguard/enforce-privacy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_packet_id: packetId,
          raw_thought_data: thoughtData
        })
      });
      if (!response.ok) throw new Error('Privacy enforcement failed');
      setPrivacyResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="neuroguard-dashboard">
      <header className="ng-header">
        <h1>🧠 NeuroGuard Architect</h1>
        <p>BCI Forensics, Neural Telemetry Analysis, & Thought Data Privacy</p>
      </header>

      {error && <div className="ng-alert">{error}</div>}

      <div className="ng-grid">
        {/* Left Column */}
        <div>
          <div className="ng-panel" style={{ marginBottom: '2rem' }}>
            <h2>📡 Deep Neural Telemetry Scan</h2>
            <form onSubmit={handleScan}>
              <div className="ng-form-group">
                <label>Subject Implant ID</label>
                <input type="text" value={subjectId} onChange={(e) => setSubjectId(e.target.value)} required />
              </div>
              <div className="ng-band-inputs">
                <div className="ng-form-group">
                  <label>Alpha (Hz)</label>
                  <input type="number" step="0.1" value={alpha} onChange={(e) => setAlpha(parseFloat(e.target.value))} required />
                </div>
                <div className="ng-form-group">
                  <label>Beta (Hz)</label>
                  <input type="number" step="0.1" value={beta} onChange={(e) => setBeta(parseFloat(e.target.value))} required />
                </div>
                <div className="ng-form-group">
                  <label>Gamma (Hz) *</label>
                  <input type="number" step="0.1" value={gamma} onChange={(e) => setGamma(parseFloat(e.target.value))} required />
                </div>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#888' }}>* High Gamma variance without biological precursor flags synthetic tampering.</p>
              <button type="submit" className="ng-btn" disabled={loading}>Analyze Brainwaves</button>
            </form>

            {scanResult && (
              <div className={`ng-scan-result ${scanResult.is_anomalous ? 'anomalous' : 'benign'}`}>
                <div style={{ fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {scanResult.is_anomalous ? `⚠️ ${scanResult.anomaly_type}` : '✅ BENIGN'}
                </div>
                {scanResult.status_message}
              </div>
            )}
          </div>

          <div className="ng-panel">
            <h2>🔒 Zero-Knowledge Privacy Enforcer</h2>
            <form onSubmit={handlePrivacy}>
              <div className="ng-form-group">
                <label>Data Packet ID</label>
                <input type="text" value={packetId} onChange={(e) => setPacketId(e.target.value)} required />
              </div>
              <div className="ng-form-group">
                <label>Raw Thought Data (Hex/String)</label>
                <input type="text" value={thoughtData} onChange={(e) => setThoughtData(e.target.value)} required />
              </div>
              <button type="submit" className="ng-btn" disabled={loading} style={{ background: '#00ccff', color: '#000' }}>Enforce Encryption</button>
            </form>

            {privacyResult && (
              <div className="ng-privacy-result">
                <div className="ng-lock-icon">🔒</div>
                <div style={{ color: '#00ff88', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {privacyResult.encryption_standard} ENCRYPTED
                </div>
                <div style={{ color: '#888' }}>{privacyResult.message}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="ng-panel">
            <h2>🔮 BCI Future Threat Simulation</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Model 20-50 year futuristic threats against neural implants to develop preemptive countermeasures.
            </p>
            <form onSubmit={handleSimulate}>
              <div className="ng-form-group">
                <label>Attack Vector</label>
                <select value={attackVector} onChange={(e) => setAttackVector(e.target.value)}>
                  <option value="MEMORY_ALTERATION">Hippocampus Memory Alteration</option>
                  <option value="MOTOR_HIJACK">Peripheral Motor Cortex Hijack</option>
                  <option value="NEURO_EAVESDROP">Optic Nerve Passive Eavesdropping</option>
                </select>
              </div>
              <button type="submit" className="ng-btn" disabled={loading} style={{ background: '#333', color: '#fff', border: '1px solid #9933ff' }}>Run Threat Model</button>
            </form>

            {simResult && (
              <div className="ng-sim-result">
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Simulated Biological Impact</div>
                  <div style={{ color: '#ff4444', fontWeight: 'bold' }}>{simResult.biological_impact}</div>
                </div>
                <div>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>System Countermeasure</div>
                  <div style={{ color: '#00ff88', fontWeight: 'bold' }}>{simResult.countermeasure_deployed}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
