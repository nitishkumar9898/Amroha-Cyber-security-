import React, { useState } from 'react';
import './QuantumSafeDashboard.css';

export const QuantumSafeDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [targetSystem, setTargetSystem] = useState('Core Banking Gateway');
  const [results, setResults] = useState<any>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const scanId = Math.random().toString(36).substring(2, 10);
      const res = await fetch('http://localhost:8000/api/quantumsafe/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_system: targetSystem, scan_id: scanId })
      });
      if (!res.ok) throw new Error('Failed to run PQC scan');
      const data = await res.json();
      setResults(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="quantumsafe-dashboard">
      <div className="qs-header">
        <h2>QuantumSafe</h2>
        <p>Post‑Quantum Cryptography Readiness & Migration</p>
      </div>
      <div className="qs-controls">
        <form onSubmit={handleScan} className="qs-form">
          <label>
            Target System
            <input
              type="text"
              value={targetSystem}
              onChange={e => setTargetSystem(e.target.value)}
            />
          </label>
          <button type="submit" disabled={loading} className="qs-scan-btn">
            {loading ? 'Scanning…' : 'Run Scan'}
          </button>
        </form>
        {error && <div className="qs-error">{error}</div>}
      </div>

      {results && (
        <div className="qs-results">
          <h3>Discovered Assets</h3>
          <table className="qs-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Algorithm</th>
                <th>Risk</th>
                <th>Q‑Day</th>
                <th>PQC</th>
                <th>Latency Δ</th>
              </tr>
            </thead>
            <tbody>
              {results.assets.map((item: any, idx: number) => {
                const { asset, vulnerability, migration } = item;
                return (
                  <tr key={idx}>
                    <td>{asset.asset_name}</td>
                    <td>{asset.algorithm}-{asset.key_size}</td>
                    <td>
                      {vulnerability ? (
                        <span className="vuln-risk">{vulnerability.criticality}</span>
                      ) : (
                        <span className="safe-label">Quantum‑Safe</span>
                      )}
                    </td>
                    <td>{vulnerability ? `T-${vulnerability.estimated_qday_years}` : '-'}</td>
                    <td>{migration ? migration.recommended_pqc : '-'}</td>
                    <td>
                      {migration ? (
                        <span className="latency-overhead">
                          +{(migration.pqc_latency_ms - migration.legacy_latency_ms).toFixed(2)}ms
                        </span>
                      ) : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default QuantumSafeDashboard;
