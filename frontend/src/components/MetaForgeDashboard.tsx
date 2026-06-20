import React, { useState } from 'react';
import './MetaForgeDashboard.css';

interface MetricResult {
  source_module: string;
  optimization_suggestion: string;
}

interface EvolutionResult {
  target_module: string;
  proposed_version: string;
  upgrade_manifest: string;
}

interface AnomalyResult {
  subsystem: string;
  severity: string;
  action_taken: string;
}

export default function MetaForgeDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Metric State
  const [sourceModule, setSourceModule] = useState('SpaceGuard');
  const [latencyMs, setLatencyMs] = useState<number>(650.0);
  const [errorRate, setErrorRate] = useState<number>(0.01);
  const [metricResult, setMetricResult] = useState<MetricResult | null>(null);

  // Evolution State
  const [targetModule, setTargetModule] = useState('NetGuard');
  const [currentVersion, setCurrentVersion] = useState('1.2.4');
  const [evolutionResult, setEvolutionResult] = useState<EvolutionResult | null>(null);

  // Anomaly State
  const [subsystem, setSubsystem] = useState('SwarmForge AI');
  const [anomalyType, setAnomalyType] = useState('BYPASS_ATTEMPT');
  const [anomalyResult, setAnomalyResult] = useState<AnomalyResult | null>(null);

  const handleMetricIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMetricResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/metaforge/ingest-metric', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_module: sourceModule,
          latency_ms: latencyMs,
          error_rate: errorRate
        })
      });
      if (!response.ok) throw new Error('Metric ingestion failed');
      setMetricResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEvolutionManage = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setEvolutionResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/metaforge/manage-evolution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_module: targetModule,
          current_version: currentVersion
        })
      });
      if (!response.ok) throw new Error('Evolution management failed');
      setEvolutionResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnomalyDetect = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAnomalyResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/metaforge/detect-anomaly', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subsystem: subsystem,
          anomaly_type: anomalyType
        })
      });
      if (!response.ok) throw new Error('Anomaly detection failed');
      setAnomalyResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="metaforge-dashboard">
      <header className="mf-header">
        <h1>👁️ MetaForge Architect</h1>
        <p>Global Platform Meta-Monitoring & Autonomous Optimization</p>
      </header>

      {error && <div className="mf-alert">{error}</div>}

      <div className="mf-grid">
        {/* Left Column */}
        <div>
          <div className="mf-panel" style={{ marginBottom: '2rem' }}>
            <h2>📊 Cross-Module Telemetry</h2>
            <form onSubmit={handleMetricIngest}>
              <div className="mf-form-group">
                <label>Source Module</label>
                <select value={sourceModule} onChange={(e) => setSourceModule(e.target.value)}>
                  <option value="SpaceGuard">SpaceGuard</option>
                  <option value="NanoQuantum">NanoQuantum</option>
                  <option value="CloudForensix">CloudForensix</option>
                  <option value="NetGuard">NetGuard</option>
                </select>
              </div>
              <div className="mf-form-group">
                <label>Latency (ms)</label>
                <input type="number" step="0.1" value={latencyMs} onChange={(e) => setLatencyMs(parseFloat(e.target.value))} required />
              </div>
              <div className="mf-form-group">
                <label>Error Rate (%)</label>
                <input type="number" step="0.01" value={errorRate} onChange={(e) => setErrorRate(parseFloat(e.target.value))} required />
              </div>
              <button type="submit" className="mf-btn" disabled={loading}>Analyze Platform Metric</button>
            </form>

            {metricResult && (
              <div className="mf-metric-result">
                <div style={{ color: '#c700ff', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Optimization Strategy Generated</div>
                <div style={{ color: '#e0e0e0', fontStyle: 'italic' }}>"{metricResult.optimization_suggestion}"</div>
              </div>
            )}
          </div>

          <div className="mf-panel">
            <h2>🧬 Autonomous Version Evolution</h2>
            <form onSubmit={handleEvolutionManage}>
              <div className="mf-form-group">
                <label>Target Module</label>
                <input type="text" value={targetModule} onChange={(e) => setTargetModule(e.target.value)} required />
              </div>
              <div className="mf-form-group">
                <label>Current Version</label>
                <input type="text" value={currentVersion} onChange={(e) => setCurrentVersion(e.target.value)} required />
              </div>
              <button type="submit" className="mf-btn" disabled={loading} style={{ background: '#00d2ff', color: '#000' }}>Draft Upgrade Manifest</button>
            </form>

            {evolutionResult && (
              <div className="mf-evolution-result">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Current Version</div>
                    <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>v{currentVersion}</div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Proposed Version</div>
                    <div style={{ color: '#00d2ff', fontWeight: 'bold', fontSize: '1.2rem' }}>v{evolutionResult.proposed_version}</div>
                  </div>
                </div>
                <div style={{ borderTop: '1px solid #333', paddingTop: '1rem' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Upgrade Manifest</div>
                  <div style={{ color: '#e0e0e0' }}>{evolutionResult.upgrade_manifest}</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="mf-panel">
            <h2>🚨 Internal Zero-Trust Scanner</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Detect meta-level threats originating from within Amroha01's own subsystems (e.g., AI governance bypasses).
            </p>
            <form onSubmit={handleAnomalyDetect}>
              <div className="mf-form-group">
                <label>Subsystem</label>
                <input type="text" value={subsystem} onChange={(e) => setSubsystem(e.target.value)} required />
              </div>
              <div className="mf-form-group">
                <label>Anomaly Signature</label>
                <select value={anomalyType} onChange={(e) => setAnomalyType(e.target.value)}>
                  <option value="BYPASS_ATTEMPT">Governance Bypass Attempt</option>
                  <option value="LATENCY_SPIKE">Unexpected Latency Spike</option>
                  <option value="UNAUTHORIZED_API">Internal API Misuse</option>
                </select>
              </div>
              <button type="submit" className="mf-btn" disabled={loading} style={{ background: '#ff4444', color: '#fff' }}>Scan for Internal Anomalies</button>
            </form>

            {anomalyResult && (
              <div className={`mf-anomaly-result ${anomalyResult.severity.toLowerCase()}`}>
                <div style={{ fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  SEVERITY: {anomalyResult.severity}
                </div>
                <div style={{ color: '#e0e0e0' }}>{anomalyResult.action_taken}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
