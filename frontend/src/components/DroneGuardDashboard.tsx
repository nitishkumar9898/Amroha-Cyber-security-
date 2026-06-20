import React, { useState } from 'react';
import './DroneGuardDashboard.css';

interface TelemetryResult {
  drone_id: string;
  gps_variance_meters: number;
  is_spoofed: boolean;
  action_taken: string;
}

interface SwarmResult {
  swarm_id: string;
  saturation_level: number;
  threat_assessment: string;
}

interface EvidenceResult {
  case_id: string;
  file_name: string;
  sha256_hash: string;
  is_compliant: boolean;
}

export default function DroneGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Telemetry State
  const [droneId, setDroneId] = useState('UAV-ALPHA-99');
  const [gpsLat, setGpsLat] = useState<number>(40.7128);
  const [gpsLon, setGpsLon] = useState<number>(-74.0060);
  const [insLat, setInsLat] = useState<number>(40.7135); // Spoofed default
  const [insLon, setInsLon] = useState<number>(-74.0065);
  const [telemetryResult, setTelemetryResult] = useState<TelemetryResult | null>(null);

  // Swarm State
  const [swarmId, setSwarmId] = useState('SWARM-ZETA');
  const [droneCount, setDroneCount] = useState<number>(500);
  const [formationType, setFormationType] = useState('HUNTER_KILLER');
  const [swarmResult, setSwarmResult] = useState<SwarmResult | null>(null);

  // Evidence State
  const [caseId, setCaseId] = useState('CASE-2026-X1');
  const [fileName, setFileName] = useState('intercept_vid_01.mp4');
  const [rawData, setRawData] = useState('binary_video_data_stream...');
  const [evidenceResult, setEvidenceResult] = useState<EvidenceResult | null>(null);

  const handleTelemetryAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTelemetryResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/droneguard/analyze-telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drone_id: droneId,
          gps_lat: gpsLat,
          gps_lon: gpsLon,
          ins_lat: insLat,
          ins_lon: insLon
        })
      });
      if (!response.ok) throw new Error('Telemetry analysis failed');
      setTelemetryResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSwarmSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSwarmResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/droneguard/simulate-swarm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          swarm_id: swarmId,
          drone_count: droneCount,
          formation_type: formationType
        })
      });
      if (!response.ok) throw new Error('Swarm simulation failed');
      setSwarmResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEvidenceSecure = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setEvidenceResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/droneguard/secure-evidence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          file_name: fileName,
          raw_data: rawData
        })
      });
      if (!response.ok) throw new Error('Evidence security failed');
      setEvidenceResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="droneguard-dashboard">
      <header className="dg-header">
        <h1>🚁 DroneGuard Architect</h1>
        <p>UAV Forensics, Swarm Warfare, & Aerial Legal Compliance</p>
      </header>

      {error && <div className="dg-alert">{error}</div>}

      <div className="dg-grid">
        {/* Left Column */}
        <div>
          <div className="dg-panel" style={{ marginBottom: '2rem' }}>
            <h2>🛰️ GPS vs INS Telemetry Analysis</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Compare external GPS coordinates against internal INS data to detect spoofing.
            </p>
            <form onSubmit={handleTelemetryAnalyze}>
              <div className="dg-form-group">
                <label>Drone ID</label>
                <input type="text" value={droneId} onChange={(e) => setDroneId(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="dg-form-group">
                  <label>GPS Latitude</label>
                  <input type="number" step="0.0001" value={gpsLat} onChange={(e) => setGpsLat(parseFloat(e.target.value))} required />
                </div>
                <div className="dg-form-group">
                  <label>GPS Longitude</label>
                  <input type="number" step="0.0001" value={gpsLon} onChange={(e) => setGpsLon(parseFloat(e.target.value))} required />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="dg-form-group">
                  <label>INS Latitude</label>
                  <input type="number" step="0.0001" value={insLat} onChange={(e) => setInsLat(parseFloat(e.target.value))} required />
                </div>
                <div className="dg-form-group">
                  <label>INS Longitude</label>
                  <input type="number" step="0.0001" value={insLon} onChange={(e) => setInsLon(parseFloat(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="dg-btn" disabled={loading}>Analyze Telemetry</button>
            </form>

            {telemetryResult && (
              <div className={`dg-telemetry-result ${telemetryResult.is_spoofed ? 'spoofed' : 'nominal'}`}>
                <div style={{ fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {telemetryResult.is_spoofed ? 'GPS SPOOFING DETECTED' : 'TELEMETRY NOMINAL'}
                </div>
                <div style={{ marginBottom: '0.5rem' }}>Variance: {telemetryResult.gps_variance_meters.toFixed(2)} meters</div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem' }}>{telemetryResult.action_taken}</div>
              </div>
            )}
          </div>

          <div className="dg-panel">
            <h2>⚖️ Aerial Evidence Chain-of-Custody</h2>
            <form onSubmit={handleEvidenceSecure}>
              <div className="dg-form-group">
                <label>Case ID</label>
                <input type="text" value={caseId} onChange={(e) => setCaseId(e.target.value)} required />
              </div>
              <div className="dg-form-group">
                <label>File Name</label>
                <input type="text" value={fileName} onChange={(e) => setFileName(e.target.value)} required />
              </div>
              <div className="dg-form-group">
                <label>Raw Data Stream</label>
                <textarea rows={3} value={rawData} onChange={(e) => setRawData(e.target.value)} required />
              </div>
              <button type="submit" className="dg-btn" disabled={loading} style={{ background: '#333', color: '#00ffcc', border: '1px solid #00ffcc' }}>Generate Legal Hash</button>
            </form>

            {evidenceResult && (
              <div className="dg-evidence-result">
                <div style={{ color: '#00ffcc', fontWeight: 'bold', marginBottom: '0.5rem' }}>✓ Evidence Secured (SHA-256)</div>
                <div style={{ fontFamily: 'monospace', color: '#888', fontSize: '0.85rem' }}>{evidenceResult.sha256_hash}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="dg-panel">
            <h2>🦅 Swarm Warfare Topology Simulator</h2>
            <form onSubmit={handleSwarmSimulate}>
              <div className="dg-form-group">
                <label>Swarm ID</label>
                <input type="text" value={swarmId} onChange={(e) => setSwarmId(e.target.value)} required />
              </div>
              <div className="dg-form-group">
                <label>Drone Count</label>
                <input type="number" value={droneCount} onChange={(e) => setDroneCount(parseInt(e.target.value))} required />
              </div>
              <div className="dg-form-group">
                <label>Formation Type</label>
                <select value={formationType} onChange={(e) => setFormationType(e.target.value)}>
                  <option value="HUNTER_KILLER">Hunter-Killer</option>
                  <option value="RECON_GRID">Recon Grid</option>
                  <option value="DEFENSE_SWARM">Defense Swarm</option>
                </select>
              </div>
              <button type="submit" className="dg-btn" disabled={loading} style={{ background: '#ffaa00', color: '#000' }}>Calculate Topology</button>
            </form>

            {swarmResult && (
              <div className="dg-swarm-result">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Swarm ID</div>
                    <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{swarmResult.swarm_id}</div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Saturation Level</div>
                    <div style={{ color: '#ffaa00', fontWeight: 'bold', fontSize: '1.2rem' }}>{swarmResult.saturation_level.toFixed(1)}</div>
                  </div>
                </div>
                <div style={{ borderTop: '1px solid #333', paddingTop: '1rem' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Threat Assessment</div>
                  <div style={{ color: '#e0e0e0' }}>{swarmResult.threat_assessment}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
