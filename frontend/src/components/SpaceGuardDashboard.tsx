import React, { useState } from 'react';
import './SpaceGuardDashboard.css';

interface SatCommResult {
  satellite_id: string;
  is_hijacked: boolean;
  status_message: string;
}

interface OrbitalSimResult {
  mission_name: string;
  orbital_risk_score: number;
  vulnerability_found: boolean;
  details: string;
}

interface AssetProtectionResult {
  asset_id: string;
  defensive_posture: string;
}

export default function SpaceGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Comm State
  const [satId, setSatId] = useState('ORBIT-X1');
  const [protocol, setProtocol] = useState('CCSDS');
  const [snr, setSnr] = useState<number>(12.5);
  const [authValid, setAuthValid] = useState<boolean>(true);
  const [commResult, setCommResult] = useState<SatCommResult | null>(null);

  // Sim State
  const [missionName, setMissionName] = useState('Project Artemis Defense');
  const [payloadType, setPayloadType] = useState('Comms Array');
  const [firmwareHash, setFirmwareHash] = useState('0x8A9B_NOMINAL_PAYLOAD');
  const [simResult, setSimResult] = useState<OrbitalSimResult | null>(null);

  // Asset State
  const [assetId, setAssetId] = useState('ORBIT-X1');
  const [threatLevel, setThreatLevel] = useState('LOW');
  const [assetResult, setAssetResult] = useState<AssetProtectionResult | null>(null);

  const handleCommAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setCommResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/spaceguard/analyze-sat-comm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          satellite_id: satId,
          protocol: protocol,
          signal_to_noise_ratio: snr,
          auth_handshake_valid: authValid
        })
      });
      if (!response.ok) throw new Error('Analysis failed');
      setCommResult(await response.json());
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
      const response = await fetch('http://localhost:8000/api/spaceguard/simulate-orbital-attack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mission_name: missionName,
          payload_type: payloadType,
          firmware_hash: firmwareHash
        })
      });
      if (!response.ok) throw new Error('Simulation failed');
      setSimResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProtect = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAssetResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/spaceguard/protect-asset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_id: assetId,
          threat_intel_level: threatLevel
        })
      });
      if (!response.ok) throw new Error('Protection strategy generation failed');
      setAssetResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="spaceguard-dashboard">
      <header className="sg-header">
        <h1>🛰️ SpaceGuard Architect</h1>
        <p>Orbital Defense, Satellite Telemetry Analysis, & Supply Chain Simulation</p>
      </header>

      {error && <div className="sg-alert">{error}</div>}

      <div className="sg-grid">
        {/* Left Column */}
        <div>
          <div className="sg-panel" style={{ marginBottom: '2rem' }}>
            <h2>📡 Satellite Telemetry Analysis</h2>
            <form onSubmit={handleCommAnalyze}>
              <div className="sg-form-group">
                <label>Satellite ID</label>
                <input type="text" value={satId} onChange={(e) => setSatId(e.target.value)} required />
              </div>
              <div className="sg-form-group">
                <label>Protocol</label>
                <select value={protocol} onChange={(e) => setProtocol(e.target.value)}>
                  <option value="CCSDS">CCSDS</option>
                  <option value="DVB-S2">DVB-S2</option>
                </select>
              </div>
              <div className="sg-form-group">
                <label>Signal-to-Noise Ratio (dB) *</label>
                <input type="number" step="0.1" value={snr} onChange={(e) => setSnr(parseFloat(e.target.value))} required />
              </div>
              <div className="sg-checkbox-group">
                <input type="checkbox" checked={authValid} onChange={(e) => setAuthValid(e.target.checked)} id="authCheck" />
                <label htmlFor="authCheck" style={{ margin: 0 }}>Valid Ground Station Auth Handshake</label>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#888' }}>* Sudden SNR drop combined with invalid auth indicates signal hijacking.</p>
              <button type="submit" className="sg-btn" disabled={loading}>Analyze Telemetry</button>
            </form>

            {commResult && (
              <div className={`sg-comm-result ${commResult.is_hijacked ? 'hijacked' : 'secure'}`}>
                <div style={{ fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {commResult.is_hijacked ? `⚠️ HIJACKING DETECTED` : '✅ SECURE'}
                </div>
                {commResult.status_message}
              </div>
            )}
          </div>

          <div className="sg-panel">
            <h2>🛡️ Orbital Asset Protection</h2>
            <form onSubmit={handleProtect}>
              <div className="sg-form-group">
                <label>Asset ID</label>
                <input type="text" value={assetId} onChange={(e) => setAssetId(e.target.value)} required />
              </div>
              <div className="sg-form-group">
                <label>Mock OSINT Threat Intel Level</label>
                <select value={threatLevel} onChange={(e) => setThreatLevel(e.target.value)}>
                  <option value="LOW">LOW</option>
                  <option value="ELEVATED">ELEVATED</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
              <button type="submit" className="sg-btn" disabled={loading} style={{ background: '#333', color: '#fff', border: '1px solid #00ccff' }}>Deploy Strategy</button>
            </form>

            {assetResult && (
              <div className="sg-asset-result">
                <div style={{ color: '#00ccff', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  STRATEGY DEPLOYED
                </div>
                <div style={{ color: '#e0e0e0' }}>{assetResult.defensive_posture}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="sg-panel">
            <h2>🚀 Orbital Supply Chain Simulator</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Simulate pre-launch vulnerabilities. Insert "COMPROMISED" into the hash to test threat detection.
            </p>
            <form onSubmit={handleSimulate}>
              <div className="sg-form-group">
                <label>Mission Name</label>
                <input type="text" value={missionName} onChange={(e) => setMissionName(e.target.value)} required />
              </div>
              <div className="sg-form-group">
                <label>Payload Type</label>
                <input type="text" value={payloadType} onChange={(e) => setPayloadType(e.target.value)} required />
              </div>
              <div className="sg-form-group">
                <label>Firmware Hash Payload</label>
                <input type="text" value={firmwareHash} onChange={(e) => setFirmwareHash(e.target.value)} required />
              </div>
              <button type="submit" className="sg-btn" disabled={loading} style={{ background: '#ff4444', color: '#fff' }}>Run Pre-Launch Sim</button>
            </form>

            {simResult && (
              <div className={`sg-sim-result ${simResult.vulnerability_found ? '' : 'safe'}`}>
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Orbital Risk Score</div>
                  <div style={{ color: simResult.vulnerability_found ? '#ff4444' : '#00ff88', fontWeight: 'bold', fontSize: '2rem' }}>
                    {simResult.orbital_risk_score.toFixed(1)} / 10.0
                  </div>
                </div>
                <div>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Details</div>
                  <div style={{ color: '#fff', fontWeight: 'bold' }}>{simResult.details}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
