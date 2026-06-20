import React, { useState } from 'react';
import './NanoQuantumDashboard.css';

interface NanoScanResult {
  device_id: string;
  is_hijacked: boolean;
  status_message: string;
}

interface NanoSimResult {
  threat_type: string;
  replication_rate: number;
  material_consumed_kg: number;
  countermeasure_deployed: string;
}

interface HardwareValidationResult {
  hardware_id: string;
  atomic_integrity_verified: boolean;
  message: string;
}

export default function NanoQuantumDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scan State
  const [deviceId, setDeviceId] = useState('NQ-SENSOR-001');
  const [electronSpin, setElectronSpin] = useState<number>(1.2);
  const [entanglementStable, setEntanglementStable] = useState<boolean>(true);
  const [scanResult, setScanResult] = useState<NanoScanResult | null>(null);

  // Sim State
  const [threatType, setThreatType] = useState('GREY_GOO');
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(60);
  const [simResult, setSimResult] = useState<NanoSimResult | null>(null);

  // HW State
  const [hardwareId, setHardwareId] = useState('HW-NQ-009');
  const [pqcAlgo, setPqcAlgo] = useState('KYBER_1024');
  const [hwResult, setHwResult] = useState<HardwareValidationResult | null>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setScanResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/nanoquantum/analyze-sensor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: deviceId,
          electron_spin_variance: electronSpin,
          entanglement_stable: entanglementStable
        })
      });
      if (!response.ok) throw new Error('Analysis failed');
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
      const response = await fetch('http://localhost:8000/api/nanoquantum/simulate-nano-threat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          threat_type: threatType,
          time_elapsed_seconds: elapsedSeconds
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

  const handleValidation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setHwResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/nanoquantum/validate-hardware', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hardware_id: hardwareId,
          pqc_algorithm_applied: pqcAlgo
        })
      });
      if (!response.ok) throw new Error('Validation failed');
      setHwResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="nanoquantum-dashboard">
      <header className="nq-header">
        <h1>🔬 NanoQuantum Architect</h1>
        <p>Sub-Molecular IoT Forensics & Self-Replicating Threat Defense</p>
      </header>

      {error && <div className="nq-alert">{error}</div>}

      <div className="nq-grid">
        {/* Left Column */}
        <div>
          <div className="nq-panel" style={{ marginBottom: '2rem' }}>
            <h2>⚛️ Quantum Sensor Telemetry Scan</h2>
            <form onSubmit={handleScan}>
              <div className="nq-form-group">
                <label>Sensor Device ID</label>
                <input type="text" value={deviceId} onChange={(e) => setDeviceId(e.target.value)} required />
              </div>
              <div className="nq-form-group">
                <label>Electron Spin Variance (Heisenberg Threshold)</label>
                <input type="number" step="0.1" value={electronSpin} onChange={(e) => setElectronSpin(parseFloat(e.target.value))} required />
              </div>
              <div className="nq-checkbox-group">
                <input type="checkbox" id="entanglement" checked={entanglementStable} onChange={(e) => setEntanglementStable(e.target.checked)} />
                <label htmlFor="entanglement" style={{ margin: 0, color: '#fff' }}>Entanglement Stable</label>
              </div>
              <button type="submit" className="nq-btn" disabled={loading}>Analyze Telemetry</button>
            </form>

            {scanResult && (
              <div className={`nq-scan-result ${scanResult.is_hijacked ? 'hijacked' : 'safe'}`}>
                <div style={{ fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {scanResult.is_hijacked ? 'HIJACK DETECTED' : 'SYSTEM NOMINAL'}
                </div>
                <div>{scanResult.status_message}</div>
              </div>
            )}
          </div>

          <div className="nq-panel">
            <h2>🛡️ Atomic Hardware Validation</h2>
            <form onSubmit={handleValidation}>
              <div className="nq-form-group">
                <label>Hardware ID</label>
                <input type="text" value={hardwareId} onChange={(e) => setHardwareId(e.target.value)} required />
              </div>
              <div className="nq-form-group">
                <label>PQC Algorithm</label>
                <select value={pqcAlgo} onChange={(e) => setPqcAlgo(e.target.value)}>
                  <option value="KYBER_1024">KYBER_1024</option>
                  <option value="DILITHIUM">DILITHIUM</option>
                  <option value="RSA_2048">RSA_2048 (Legacy)</option>
                </select>
              </div>
              <button type="submit" className="nq-btn" disabled={loading} style={{ background: '#333', color: '#fff', border: '1px solid #00ffff' }}>Validate Integrity</button>
            </form>

            {hwResult && (
              <div className="nq-hardware-result">
                <div style={{ color: hwResult.atomic_integrity_verified ? '#00ffff' : '#ff4444', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {hwResult.atomic_integrity_verified ? 'VERIFIED' : 'FAILED'}
                </div>
                <div style={{ color: '#e0e0e0' }}>{hwResult.message}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="nq-panel">
            <h2>🦠 Self-Replicating Threat Simulator</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Model exponential "Grey Goo" scenarios and visualize material consumption rates before deploying countermeasures.
            </p>
            <form onSubmit={handleSimulate}>
              <div className="nq-form-group">
                <label>Threat Vector</label>
                <select value={threatType} onChange={(e) => setThreatType(e.target.value)}>
                  <option value="GREY_GOO">Grey Goo (Material Devourer)</option>
                  <option value="NANOBOT_SWARM">Weaponized Nanobot Swarm</option>
                </select>
              </div>
              <div className="nq-form-group">
                <label>Time Elapsed (Seconds)</label>
                <input type="number" value={elapsedSeconds} onChange={(e) => setElapsedSeconds(parseInt(e.target.value))} required />
              </div>
              <button type="submit" className="nq-btn" disabled={loading} style={{ background: '#ff4444', color: '#fff' }}>Run Swarm Simulation</button>
            </form>

            {simResult && (
              <div className="nq-sim-result">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Replication Base</div>
                    <div style={{ color: '#ff4444', fontWeight: 'bold', fontSize: '1.5rem' }}>
                      {simResult.replication_rate.toFixed(2)}x
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Material Consumed</div>
                    <div style={{ color: '#ffcc00', fontWeight: 'bold', fontSize: '1.5rem' }}>
                      {simResult.material_consumed_kg.toFixed(3)} kg
                    </div>
                  </div>
                </div>
                <div style={{ borderTop: '1px solid #333', paddingTop: '1rem' }}>
                  <div style={{ color: '#00ffff', fontSize: '0.8rem', textTransform: 'uppercase' }}>Countermeasure Deployed</div>
                  <div style={{ color: '#fff' }}>{simResult.countermeasure_deployed}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
