import React, { useState } from 'react';
import './CloudForensixDashboard.css';

// Types representing API responses
interface Incident {
  id: number;
  provider: string;
  severity: string;
  status: string;
}

interface LogAnalysisResult {
  analyzed_count: number;
  anomalies_detected: number;
  findings: string[];
}

interface ContainerScanResult {
  image_hash: string;
  escape_detected: boolean;
  vulnerabilities: string[];
}

interface ServerlessTraceResult {
  function_name: string;
  execution_path: string[];
  malicious_payload_detected: boolean;
}

interface ComplianceResult {
  is_compliant: boolean;
  violations: string[];
}

export default function CloudForensixDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [incident, setIncident] = useState<Incident | null>(null);
  const [logAnalysis, setLogAnalysis] = useState<LogAnalysisResult | null>(null);
  const [containerScan, setContainerScan] = useState<ContainerScanResult | null>(null);
  const [serverlessTrace, setServerlessTrace] = useState<ServerlessTraceResult | null>(null);
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);

  // Form State
  const [provider, setProvider] = useState('AWS');
  const [severity, setSeverity] = useState('HIGH');

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/cloudforensix/incidents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, severity })
      });
      if (!response.ok) throw new Error('Failed to create incident');
      setIncident(await response.json());
      
      // Reset other states
      setLogAnalysis(null);
      setContainerScan(null);
      setServerlessTrace(null);
      setCompliance(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeLogs = async () => {
    if (!incident) return;
    setLoading(true);
    try {
      // Mock log payload for demonstration
      const mockLogs = [
        { eventName: "AssumeRole", region: "us-east-1" },
        { eventName: "CreateUser", region: "eu-west-3" }, // anomalous region
        { eventName: "DeleteTrail", region: "us-east-1" }, // anomalous action
        { eventName: "S3Transfer", sourceRegion: "eu-central-1", destRegion: "us-east-1" } // GDPR violation
      ];

      const response = await fetch('http://localhost:8000/api/cloudforensix/analyze-logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incident.id,
          log_source: 'CloudTrail',
          raw_logs: mockLogs
        })
      });
      if (!response.ok) throw new Error('Failed to analyze logs');
      setLogAnalysis(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScanContainer = async () => {
    if (!incident) return;
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/cloudforensix/scan-container', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incident.id,
          image_hash: 'sha256:bad_actor_img_v2',
          namespace: 'kube-system'
        })
      });
      if (!response.ok) throw new Error('Failed to scan container');
      setContainerScan(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTraceServerless = async () => {
    if (!incident) return;
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/cloudforensix/trace-serverless', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incident.id,
          function_name: 'crypto_miner_lambda_01'
        })
      });
      if (!response.ok) throw new Error('Failed to trace serverless function');
      setServerlessTrace(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckResidency = async () => {
    if (!incident) return;
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/cloudforensix/residency-compliance/${incident.id}`);
      if (!response.ok) throw new Error('Failed to check residency');
      setCompliance(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="cloud-forensix-dashboard">
      <header className="cf-header">
        <h1>☁️ CloudForensix Architect</h1>
        <p>Multi-Cloud, Kubernetes, and Serverless Environment Investigations</p>
      </header>

      {error && <div className="cf-alert">{error}</div>}

      <div className="cf-grid">
        {/* Left Column: Incident Control */}
        <div className="cf-panel" style={{ height: 'fit-content' }}>
          <h2>🚨 Incident Initialization</h2>
          <form onSubmit={handleCreateIncident}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#888' }}>Cloud Provider</label>
              <select value={provider} onChange={(e) => setProvider(e.target.value)} style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-tertiary)', color: '#fff', border: '1px solid var(--border-color)' }}>
                <option value="AWS">AWS</option>
                <option value="AZURE">Azure</option>
                <option value="GCP">GCP</option>
                <option value="MULTI">Multi-Cloud</option>
              </select>
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#888' }}>Initial Severity</label>
              <select value={severity} onChange={(e) => setSeverity(e.target.value)} style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-tertiary)', color: '#fff', border: '1px solid var(--border-color)' }}>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            <button type="submit" className="cf-btn" disabled={loading}>Open Investigation</button>
          </form>

          {incident && (
            <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
              <h3 style={{ color: '#44ccff', marginBottom: '1rem' }}>Active Incident #{incident.id}</h3>
              
              <button onClick={handleAnalyzeLogs} className="cf-btn" disabled={loading}>
                1. Analyze Multi-Cloud Logs
              </button>
              <button onClick={handleScanContainer} className="cf-btn" disabled={loading}>
                2. Scan Container Workloads
              </button>
              <button onClick={handleTraceServerless} className="cf-btn" disabled={loading}>
                3. Trace Serverless Functions
              </button>
              <button onClick={handleCheckResidency} className="cf-btn" disabled={loading || !logAnalysis}>
                4. Audit Data Residency
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Evidence & Analysis View */}
        <div className="cf-panel" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <h2>📊 Investigation Board</h2>
          
          {!incident ? (
            <p style={{ color: '#888', textAlign: 'center', marginTop: '2rem' }}>Open an investigation to view evidence.</p>
          ) : (
            <>
              {/* Log Analysis Results */}
              {logAnalysis && (
                <div>
                  <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>CloudTrail / Audit Logs</h3>
                  <div className="cf-metrics">
                    <div className="cf-metric-card">
                      <span className="val">{logAnalysis.analyzed_count}</span>
                      <span className="label">Logs Parsed</span>
                    </div>
                    <div className="cf-metric-card">
                      <span className="val" style={{ color: logAnalysis.anomalies_detected > 0 ? '#ff4444' : '#44ff44' }}>
                        {logAnalysis.anomalies_detected}
                      </span>
                      <span className="label">Anomalies</span>
                    </div>
                  </div>
                  <div>
                    {logAnalysis.findings.map((f, i) => (
                      <div key={i} className="cf-log-entry anomalous">
                        <span className="cf-finding">DETECTED:</span> {f}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Container Scan Results */}
              {containerScan && (
                <div>
                  <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Kubernetes Forensics</h3>
                  <div className="cf-log-entry" style={{ borderColor: containerScan.escape_detected ? '#ff4444' : '#44ff44' }}>
                    <p><strong>Image:</strong> {containerScan.image_hash}</p>
                    <p><strong>Container Escape Detected:</strong> {containerScan.escape_detected ? 'YES (Critical)' : 'NO'}</p>
                    <p style={{ marginTop: '0.5rem', color: '#888' }}>Vulnerabilities: {containerScan.vulnerabilities.join(', ')}</p>
                  </div>
                </div>
              )}

              {/* Serverless Trace Results */}
              {serverlessTrace && (
                <div>
                  <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Serverless Trace: {serverlessTrace.function_name}</h3>
                  <div className="trace-tree">
                    {serverlessTrace.execution_path.map((node, i) => (
                      <div key={i} className="trace-node">{node}</div>
                    ))}
                  </div>
                  {serverlessTrace.malicious_payload_detected && (
                    <div className="cf-alert" style={{ marginTop: '1rem' }}>
                      Malicious payload / unauthorized outbound connection detected in execution context!
                    </div>
                  )}
                </div>
              )}

              {/* Compliance Results */}
              {compliance && (
                <div>
                  <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Data Residency Audit</h3>
                  <div className={`compliance-status ${compliance.is_compliant ? 'pass' : 'fail'}`}>
                    {compliance.is_compliant ? 'COMPLIANT' : 'VIOLATION DETECTED'}
                  </div>
                  {!compliance.is_compliant && (
                    <div style={{ marginTop: '1rem' }}>
                      {compliance.violations.map((v, i) => (
                        <div key={i} style={{ color: '#ff4444' }}>• {v}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
