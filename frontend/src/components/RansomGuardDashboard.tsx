import React, { useState } from 'react';
import './RansomGuardDashboard.css';

// Types representing the API responses
interface Incident {
  id: number;
  status: string;
  target_entity: string;
}

interface TraceHop {
  from_address: string;
  to_address: string;
  amount: number;
  risk_score: number;
}

interface Wallet {
  address: string;
  wallet_type: string;
  balance: number;
}

interface TraceReport {
  incident_id: number;
  wallets_identified: Wallet[];
  transaction_graph: TraceHop[];
  attribution: string;
  variant_analysis: {
    variant: string;
    is_decryptable: boolean;
    simulated_decryption_key: string | null;
  };
  osint_summary: string;
}

export default function RansomGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [traceReport, setTraceReport] = useState<TraceReport | null>(null);
  const [complianceHash, setComplianceHash] = useState<string | null>(null);

  // Form states
  const [targetEntity, setTargetEntity] = useState('Acme Corp');
  const [ransomNote, setRansomNote] = useState('Your files are encrypted by Ryuk. Send 5 BTC.');
  const [demandedAmount, setDemandedAmount] = useState<number>(5.0);
  const [initialWallet, setInitialWallet] = useState('bc1q_test_1234');

  const handleReportIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/ransomguard/incidents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_entity: targetEntity,
          ransom_note: ransomNote,
          demanded_amount: demandedAmount,
          currency: 'BTC'
        })
      });
      if (!response.ok) throw new Error('Failed to report incident');
      const data = await response.json();
      setIncident(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTraceFunds = async () => {
    if (!incident) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/ransomguard/trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incident.id,
          initial_wallet_address: initialWallet
        })
      });
      if (!response.ok) throw new Error('Failed to trace funds');
      const data = await response.json();
      setTraceReport(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCompliance = async () => {
    if (!incident) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/ransomguard/compliance/${incident.id}`);
      if (!response.ok) throw new Error('Failed to generate compliance report');
      const data = await response.json();
      setComplianceHash(data.chain_of_custody_hash);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ransom-guard-dashboard">
      <header className="rg-header">
        <h1>💸 RansomGuard Architect</h1>
        <p>Advanced Ransomware Forensics & Crypto-Crime Tracking</p>
      </header>

      {error && <div className="rg-alert">{error}</div>}

      <div className="rg-grid">
        {/* Left Column: Incident Reporting */}
        <div className="rg-panel">
          <h2>📝 Report Incident</h2>
          <form onSubmit={handleReportIncident}>
            <div className="rg-form-group">
              <label>Target Entity</label>
              <input value={targetEntity} onChange={(e) => setTargetEntity(e.target.value)} required />
            </div>
            <div className="rg-form-group">
              <label>Demanded Amount (BTC)</label>
              <input type="number" step="0.1" value={demandedAmount} onChange={(e) => setDemandedAmount(parseFloat(e.target.value))} required />
            </div>
            <div className="rg-form-group">
              <label>Ransom Note Content</label>
              <textarea value={ransomNote} onChange={(e) => setRansomNote(e.target.value)} required />
            </div>
            <button type="submit" className="rg-btn" disabled={loading}>
              {loading ? 'Processing...' : 'Register Incident'}
            </button>
          </form>

          {incident && (
            <div style={{ marginTop: '2rem' }}>
              <h3>Incident Logged: #{incident.id}</h3>
              <div className="rg-form-group">
                <label>Initial Malicious Wallet</label>
                <input value={initialWallet} onChange={(e) => setInitialWallet(e.target.value)} />
              </div>
              <button onClick={handleTraceFunds} className="rg-btn" style={{ background: '#44ccff' }} disabled={loading}>
                Initiate AI Wallet Trace
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Tracing & Analysis Results */}
        <div className="rg-panel">
          <h2>🔍 Forensic Analysis</h2>
          
          {!traceReport ? (
            <p style={{ color: '#888' }}>No tracing data available. Report an incident and initiate a trace to begin.</p>
          ) : (
            <div className="trace-results">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                <div style={{ background: 'var(--bg-tertiary)', padding: '1rem', borderRadius: '4px' }}>
                  <h4>Variant Detection</h4>
                  <p style={{ color: '#ff4444', fontWeight: 'bold' }}>{traceReport.variant_analysis.variant}</p>
                  <p>Decryptable: <span style={{ color: traceReport.variant_analysis.is_decryptable ? '#44ff44' : '#ff4444' }}>
                    {traceReport.variant_analysis.is_decryptable ? 'YES' : 'NO'}
                  </span></p>
                  {traceReport.variant_analysis.simulated_decryption_key && (
                    <p style={{ fontSize: '0.8rem', fontFamily: 'monospace' }}>Key: {traceReport.variant_analysis.simulated_decryption_key.substring(0, 16)}...</p>
                  )}
                </div>
                
                <div style={{ background: 'var(--bg-tertiary)', padding: '1rem', borderRadius: '4px' }}>
                  <h4>Actor Attribution & OSINT</h4>
                  <p style={{ color: '#44ccff', fontWeight: 'bold' }}>{traceReport.attribution}</p>
                  <p style={{ fontSize: '0.9rem', color: '#b0b0b0', marginTop: '0.5rem' }}>{traceReport.osint_summary}</p>
                </div>
              </div>

              <h3>Transaction Trace Hops</h3>
              <div className="trace-flow">
                {traceReport.transaction_graph.map((hop, idx) => (
                  <div key={idx} className={`trace-hop ${hop.risk_score > 0.9 ? 'high-risk' : ''}`}>
                    <div className="hop-details">
                      <span className="hop-address">From: {hop.from_address}</span>
                      <span className="hop-address">To: {hop.to_address}</span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className="hop-amount">{hop.amount.toFixed(2)} BTC</div>
                      <div style={{ fontSize: '0.8rem', color: '#888' }}>Risk: {hop.risk_score.toFixed(2)}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="compliance-box">
                <button onClick={handleGenerateCompliance} className="rg-btn" style={{ background: '#44ff44', color: '#000' }} disabled={loading}>
                  Generate Legal Compliance Report
                </button>
                {complianceHash && (
                  <div style={{ marginTop: '1rem' }}>
                    <strong>Chain of Custody Registered:</strong>
                    <div className="hash-string">SHA256: {complianceHash}</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
