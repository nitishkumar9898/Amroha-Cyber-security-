import React, { useState } from 'react';
import './ResilientForgeDashboard.css';

interface SimulationReport {
  scenario_name: string;
  target_infrastructure: string;
  optimized_rto_hours: number;
  optimization_strategy: string;
}

interface BackupVerifyResult {
  backup_id: string;
  is_corrupt: boolean;
  malware_detected: boolean;
  status_message: string;
}

interface HealResult {
  asset_id: string;
  final_state: string;
  reconstruction_method: string;
}

export default function ResilientForgeDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sim State
  const [scenarioName, setScenarioName] = useState('RANSOMWARE');
  const [targetInfra, setTargetInfra] = useState('Core-DB-Cluster');
  const [initialDowntime, setInitialDowntime] = useState<number>(24.0);
  const [simReport, setSimReport] = useState<SimulationReport | null>(null);

  // Backup State
  const [backupId, setBackupId] = useState('BKP-2026-06-20');
  const [fileSignature, setFileSignature] = useState('CLEAN_HASH_XYZ');
  const [backupResult, setBackupResult] = useState<BackupVerifyResult | null>(null);

  // Heal State
  const [assetId, setAssetId] = useState('Core-DB-Cluster-01');
  const [initialState, setInitialState] = useState('CORRUPTED');
  const [healResult, setHealResult] = useState<HealResult | null>(null);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSimReport(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/resilientforge/simulate-disaster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_name: scenarioName,
          target_infrastructure: targetInfra,
          simulated_downtime_hours: initialDowntime
        })
      });
      if (!response.ok) throw new Error('Simulation failed');
      setSimReport(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyBackup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setBackupResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/resilientforge/verify-backup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          backup_id: backupId,
          file_signature: fileSignature
        })
      });
      if (!response.ok) throw new Error('Verification failed');
      setBackupResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleHeal = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setHealResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/resilientforge/trigger-heal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_id: assetId,
          initial_state: initialState
        })
      });
      if (!response.ok) throw new Error('Heal protocol failed');
      setHealResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="resilientforge-dashboard">
      <header className="rf-header">
        <h1>🛡️ ResilientForge Architect</h1>
        <p>Cyber Disaster Recovery, RTO Optimization, and Self-Healing Infrastructure</p>
      </header>

      {error && <div className="rf-alert">{error}</div>}

      <div className="rf-grid">
        {/* Left Column */}
        <div>
          <div className="rf-panel" style={{ marginBottom: '2rem' }}>
            <h2>🌪️ Run Disaster Simulation</h2>
            <form onSubmit={handleSimulate}>
              <div className="rf-form-group">
                <label>Scenario</label>
                <select value={scenarioName} onChange={(e) => setScenarioName(e.target.value)}>
                  <option value="RANSOMWARE">Ransomware Outbreak</option>
                  <option value="DATACENTER_FIRE">Datacenter Fire / Physical Loss</option>
                  <option value="DDOS_OUTAGE">Volumetric DDoS Outage</option>
                </select>
              </div>
              <div className="rf-form-group">
                <label>Target Infrastructure</label>
                <input type="text" value={targetInfra} onChange={(e) => setTargetInfra(e.target.value)} required />
              </div>
              <div className="rf-form-group">
                <label>Est. Standard Downtime (Hours)</label>
                <input type="number" step="0.1" value={initialDowntime} onChange={(e) => setInitialDowntime(parseFloat(e.target.value))} required />
              </div>
              <button type="submit" className="rf-btn" disabled={loading}>Generate RTO Strategy</button>
            </form>

            {simReport && (
              <div className="rf-sim-result">
                <div style={{ color: '#888', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 'bold' }}>AI-Optimized RTO</div>
                <div className="rf-rto-time">{simReport.optimized_rto_hours} <span style={{ fontSize: '1.5rem' }}>HRS</span></div>
                <div style={{ background: '#111', padding: '1rem', borderRadius: '4px', textAlign: 'left', marginTop: '1rem', border: '1px solid #333' }}>
                  <strong style={{ color: '#00ccff' }}>STRATEGY:</strong><br/>
                  {simReport.optimization_strategy}
                </div>
              </div>
            )}
          </div>

          <div className="rf-panel">
            <h2>💾 Verify Backup Integrity</h2>
            <form onSubmit={handleVerifyBackup}>
              <div className="rf-form-group">
                <label>Backup Manifest ID</label>
                <input type="text" value={backupId} onChange={(e) => setBackupId(e.target.value)} required />
              </div>
              <div className="rf-form-group">
                <label>File Signature (Mock Payload)</label>
                <input type="text" value={fileSignature} onChange={(e) => setFileSignature(e.target.value)} required placeholder="e.g. CLEAN_HASH_XYZ or HASH_CORRUPT_MALWARE" />
              </div>
              <button type="submit" className="rf-btn" disabled={loading} style={{ background: '#333', color: '#fff' }}>Scan Backup</button>
            </form>

            {backupResult && (
              <div className={`rf-backup-result ${backupResult.is_corrupt || backupResult.malware_detected ? 'corrupt' : 'clean'}`}>
                {backupResult.status_message}
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="rf-panel">
            <h2>⚕️ Auto-Healing Orchestration</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Initiate forensic reconstruction on a compromised asset.
            </p>
            <form onSubmit={handleHeal}>
              <div className="rf-form-group">
                <label>Asset ID</label>
                <input type="text" value={assetId} onChange={(e) => setAssetId(e.target.value)} required />
              </div>
              <div className="rf-form-group">
                <label>Initial State</label>
                <select value={initialState} onChange={(e) => setInitialState(e.target.value)}>
                  <option value="CORRUPTED">CORRUPTED (Ransomware/Wiper)</option>
                  <option value="OFFLINE">OFFLINE (Hardware Failure)</option>
                </select>
              </div>
              <button type="submit" className="rf-btn" disabled={loading} style={{ background: '#ffaa00', color: '#000' }}>Initiate Self-Heal Protocol</button>
            </form>

            {healResult && (
              <div className="rf-heal-result">
                <div className="rf-heal-state">
                  <span className="rf-state-badge corrupted">{initialState}</span>
                  <span className="rf-arrow">➔</span>
                  <span className="rf-state-badge healed">{healResult.final_state}</span>
                </div>
                <div style={{ color: '#888', fontSize: '0.9rem' }}>
                  <strong>Reconstruction Method:</strong> {healResult.reconstruction_method}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
