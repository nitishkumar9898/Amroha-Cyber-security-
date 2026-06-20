import React, { useState } from 'react';
import './FinGuardDashboard.css';

interface AnomalyResult {
  transaction_id: string;
  is_anomalous: boolean;
  action_taken: string;
}

interface TraceResult {
  trace_id: string;
  complexity_score: number;
  crosses_borders: boolean;
  trace_status: string;
}

interface LaunderingResult {
  entity_id: string;
  pattern_type: string;
  risk_level: string;
}

interface ComplianceResult {
  report_id: string;
  agency: string;
  report_hash: string;
  submission_status: string;
}

export default function FinGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Anomaly State
  const [txId, setTxId] = useState('TX-99901');
  const [amount, setAmount] = useState<number>(75000.0);
  const [velocity, setVelocity] = useState<number>(12.5);
  const [anomalyResult, setAnomalyResult] = useState<AnomalyResult | null>(null);

  // Trace State
  const [traceId, setTraceId] = useState('TRACE-XYZ');
  const [hopSequence, setHopSequence] = useState('UPI->CRYPTO_MIXER->SWIFT_CAYMAN');
  const [traceResult, setTraceResult] = useState<TraceResult | null>(null);

  // Laundering State
  const [entityId, setEntityId] = useState('ENTITY-404');
  const [txCount, setTxCount] = useState<number>(60);
  const [avgAmount, setAvgAmount] = useState<number>(9500.0);
  const [osintFlag, setOsintFlag] = useState<boolean>(true);
  const [ransomFlag, setRansomFlag] = useState<boolean>(false);
  const [launderingResult, setLaunderingResult] = useState<LaunderingResult | null>(null);

  // Compliance State
  const [agency, setAgency] = useState('FIU-IND');
  const [rawData, setRawData] = useState('{...suspicious activity report...}');
  const [complianceResult, setComplianceResult] = useState<ComplianceResult | null>(null);

  const handleDetectAnomaly = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAnomalyResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/finguard/detect-anomaly', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: txId,
          amount: amount,
          velocity_score: velocity
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

  const handleTracePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTraceResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/finguard/trace-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trace_id: traceId,
          hop_sequence: hopSequence
        })
      });
      if (!response.ok) throw new Error('Payment tracing failed');
      setTraceResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeLaundering = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLaunderingResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/finguard/analyze-laundering', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_id: entityId,
          transaction_count: txCount,
          average_amount: avgAmount,
          osint_threat_intel: osintFlag,
          ransomware_watchlist: ransomFlag
        })
      });
      if (!response.ok) throw new Error('Laundering analysis failed');
      setLaunderingResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCompliance = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setComplianceResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/finguard/generate-compliance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agency: agency,
          raw_financial_data: rawData
        })
      });
      if (!response.ok) throw new Error('Compliance generation failed');
      setComplianceResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="finguard-dashboard">
      <header className="fg-header">
        <h1>🏦 FinGuard Architect</h1>
        <p>Digital Payment Forensics, SWIFT Tracing, & Anti-Money Laundering (AML)</p>
      </header>

      {error && <div className="fg-alert">{error}</div>}

      <div className="fg-grid">
        {/* Left Column */}
        <div>
          <div className="fg-panel" style={{ marginBottom: '2rem' }}>
            <h2>⚡ Real-Time Anomaly Detection</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Detect fraudulent bursts by analyzing transaction velocity and cumulative volume.
            </p>
            <form onSubmit={handleDetectAnomaly}>
              <div className="fg-form-group">
                <label>Transaction ID</label>
                <input type="text" value={txId} onChange={(e) => setTxId(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="fg-form-group">
                  <label>Amount (USD)</label>
                  <input type="number" step="0.01" value={amount} onChange={(e) => setAmount(parseFloat(e.target.value))} required />
                </div>
                <div className="fg-form-group">
                  <label>Velocity (Tx/min)</label>
                  <input type="number" step="0.1" value={velocity} onChange={(e) => setVelocity(parseFloat(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="fg-btn" disabled={loading}>Analyze Transaction</button>
            </form>

            {anomalyResult && (
              <div className={`fg-result-box ${anomalyResult.is_anomalous ? 'danger' : 'nominal'}`}>
                <div className="fg-result-title" style={{ color: anomalyResult.is_anomalous ? '#ff4444' : '#00ffcc' }}>
                  {anomalyResult.is_anomalous ? 'FRAUD ALERT' : 'TRANSACTION NOMINAL'}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem' }}>{anomalyResult.action_taken}</div>
              </div>
            )}
          </div>

          <div className="fg-panel">
            <h2>🌍 Cross-Border Payment Tracing</h2>
            <form onSubmit={handleTracePayment}>
              <div className="fg-form-group">
                <label>Trace ID</label>
                <input type="text" value={traceId} onChange={(e) => setTraceId(e.target.value)} required />
              </div>
              <div className="fg-form-group">
                <label>Hop Sequence (e.g., UPI-&gt;CRYPTO-&gt;SWIFT)</label>
                <input type="text" value={hopSequence} onChange={(e) => setHopSequence(e.target.value)} required />
              </div>
              <button type="submit" className="fg-btn" disabled={loading} style={{ background: '#333', color: '#fca311', border: '1px solid #fca311' }}>Trace Financial Routing</button>
            </form>

            {traceResult && (
              <div className="fg-result-box warning">
                <div className="fg-result-title" style={{ color: '#fca311' }}>{traceResult.trace_status}</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Complexity Score</div>
                    <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{traceResult.complexity_score.toFixed(1)}</div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Crosses Borders</div>
                    <div style={{ color: traceResult.crosses_borders ? '#ff4444' : '#00ffcc', fontWeight: 'bold' }}>
                      {traceResult.crosses_borders ? 'YES (High Risk)' : 'NO (Domestic)'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="fg-panel" style={{ marginBottom: '2rem' }}>
            <h2>🕵️ AML Pattern Recognition</h2>
            <form onSubmit={handleAnalyzeLaundering}>
              <div className="fg-form-group">
                <label>Entity/Account ID</label>
                <input type="text" value={entityId} onChange={(e) => setEntityId(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="fg-form-group">
                  <label>Transaction Count</label>
                  <input type="number" value={txCount} onChange={(e) => setTxCount(parseInt(e.target.value))} required />
                </div>
                <div className="fg-form-group">
                  <label>Average Amount</label>
                  <input type="number" step="0.01" value={avgAmount} onChange={(e) => setAvgAmount(parseFloat(e.target.value))} required />
                </div>
              </div>
              <div style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
                <div className="fg-form-group" style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <input type="checkbox" id="osintCheck" checked={osintFlag} onChange={(e) => setOsintFlag(e.target.checked)} />
                  <label htmlFor="osintCheck" style={{ margin: 0, color: '#e0e0e0' }}>OSINT Threat Intel Match</label>
                </div>
                <div className="fg-form-group" style={{ display: 'flex', alignItems: 'center' }}>
                  <input type="checkbox" id="ransomCheck" checked={ransomFlag} onChange={(e) => setRansomFlag(e.target.checked)} />
                  <label htmlFor="ransomCheck" style={{ margin: 0, color: '#e0e0e0' }}>RansomGuard Watchlist Match</label>
                </div>
              </div>
              <button type="submit" className="fg-btn" disabled={loading} style={{ background: '#ff4444', color: '#fff' }}>Analyze Laundering Risk</button>
            </form>

            {launderingResult && (
              <div className={`fg-result-box ${launderingResult.risk_level === 'CRITICAL' ? 'danger' : (launderingResult.risk_level === 'HIGH' ? 'warning' : 'nominal')}`}>
                <div className="fg-result-title" style={{ color: launderingResult.risk_level === 'CRITICAL' ? '#ff4444' : '#fca311' }}>
                  RISK LEVEL: {launderingResult.risk_level}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem' }}>Pattern Detected: {launderingResult.pattern_type}</div>
              </div>
            )}
          </div>

          <div className="fg-panel">
            <h2>📜 Regulatory Compliance</h2>
            <form onSubmit={handleGenerateCompliance}>
              <div className="fg-form-group">
                <label>Regulatory Agency</label>
                <select value={agency} onChange={(e) => setAgency(e.target.value)}>
                  <option value="FIU-IND">FIU-IND (India)</option>
                  <option value="RBI">RBI (India)</option>
                  <option value="FINCEN">FinCEN (USA)</option>
                  <option value="FCA">FCA (UK)</option>
                </select>
              </div>
              <div className="fg-form-group">
                <label>Raw Suspicious Activity Report (SAR)</label>
                <textarea rows={3} value={rawData} onChange={(e) => setRawData(e.target.value)} required />
              </div>
              <button type="submit" className="fg-btn" disabled={loading} style={{ background: '#4facfe', color: '#fff' }}>Generate Compliance Hash</button>
            </form>

            {complianceResult && (
              <div className="fg-result-box info">
                <div className="fg-result-title" style={{ color: '#4facfe' }}>✓ Report Ready ({complianceResult.agency})</div>
                <div style={{ margin: '1rem 0' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Report ID</div>
                  <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{complianceResult.report_id}</div>
                </div>
                <div>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>SHA-256 Signature</div>
                  <div style={{ fontFamily: 'monospace', color: '#4facfe', fontSize: '0.85rem', wordBreak: 'break-all' }}>
                    {complianceResult.report_hash}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
