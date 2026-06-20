import React, { useState } from 'react';
import './GlobalJurixDashboard.css';

interface JurisdictionResult {
  case_id: string;
  primary_legal_framework: string;
  jurisdiction_conflict: boolean;
  routing_advice: string;
}

interface EvidenceResult {
  evidence_id: string;
  file_hash: string;
  encryption_standard: string;
  is_compliant: boolean;
}

interface MLATResult {
  treaty_status: string;
  estimated_processing_days: number;
  expedited_routing_available: boolean;
}

interface LinkResult {
  status: string;
  case_id: string;
  agency_code: string;
}

export default function GlobalJurixDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Jurisdiction State
  const [caseId, setCaseId] = useState('CASE-101');
  const [sourceCountry, setSourceCountry] = useState('Russia');
  const [targetCountry, setTargetCountry] = useState('Germany');
  const [jurisdictionResult, setJurisdictionResult] = useState<JurisdictionResult | null>(null);

  // Evidence State
  const [evidenceId, setEvidenceId] = useState('EVID-55');
  const [rawData, setRawData] = useState('PCAP_DATA_12345');
  const [evidenceResult, setEvidenceResult] = useState<EvidenceResult | null>(null);

  // MLAT State
  const [reqCountry, setReqCountry] = useState('USA');
  const [recCountry, setRecCountry] = useState('UK');
  const [mlatResult, setMlatResult] = useState<MLATResult | null>(null);

  // Link State
  const [linkCaseId, setLinkCaseId] = useState('CASE-101');
  const [agencyCode, setAgencyCode] = useState('INTERPOL');
  const [linkResult, setLinkResult] = useState<LinkResult | null>(null);

  const handleMapJurisdiction = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setJurisdictionResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/globaljurix/map-jurisdiction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          source_country: sourceCountry,
          target_country: targetCountry
        })
      });
      if (!response.ok) throw new Error('Jurisdiction mapping failed');
      setJurisdictionResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePackageEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setEvidenceResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/globaljurix/package-evidence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          evidence_id: evidenceId,
          raw_data_string: rawData
        })
      });
      if (!response.ok) throw new Error('Evidence packaging failed');
      setEvidenceResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckMlat = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMlatResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/globaljurix/check-mlat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requesting_country: reqCountry,
          receiving_country: recCountry
        })
      });
      if (!response.ok) throw new Error('MLAT check failed');
      setMlatResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkModule = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLinkResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/globaljurix/link-collabguard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: linkCaseId,
          agency_code: agencyCode
        })
      });
      if (!response.ok) throw new Error('Agency linking failed');
      setLinkResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="globaljurix-dashboard">
      <header className="gj-header">
        <h1>⚖️ GlobalJurix Architect</h1>
        <p>International Cyber Law, Jurisdiction Mapping, and MLAT Treaties</p>
      </header>

      {error && <div className="gj-alert">{error}</div>}

      <div className="gj-grid">
        {/* Left Column */}
        <div>
          <div className="gj-panel" style={{ marginBottom: '2rem' }}>
            <h2>🌍 Jurisdiction Mapper</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Map applicable legal frameworks (e.g. GDPR, CLOUD Act) based on cyber attack origin and target vectors.
            </p>
            <form onSubmit={handleMapJurisdiction}>
              <div className="gj-form-group">
                <label>Case ID</label>
                <input type="text" value={caseId} onChange={(e) => setCaseId(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="gj-form-group">
                  <label>Attacker/Source Country</label>
                  <input type="text" value={sourceCountry} onChange={(e) => setSourceCountry(e.target.value)} required />
                </div>
                <div className="gj-form-group">
                  <label>Victim/Target Country</label>
                  <input type="text" value={targetCountry} onChange={(e) => setTargetCountry(e.target.value)} required />
                </div>
              </div>
              <button type="submit" className="gj-btn" disabled={loading}>Map Jurisdiction</button>
            </form>

            {jurisdictionResult && (
              <div className={`gj-result-box ${jurisdictionResult.jurisdiction_conflict ? 'danger' : 'nominal'}`}>
                <div className="gj-result-title" style={{ color: jurisdictionResult.jurisdiction_conflict ? '#ff4444' : '#00ffcc' }}>
                  {jurisdictionResult.jurisdiction_conflict ? 'CONFLICT DETECTED' : 'CLEAR JURISDICTION'}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem', marginTop: '1rem' }}>
                  <div>
                    <span style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Framework: </span>
                    <span style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{jurisdictionResult.primary_legal_framework}</span>
                  </div>
                  <div>
                    <span style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Advice: </span>
                    <span style={{ color: '#e0e0e0' }}>{jurisdictionResult.routing_advice}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="gj-panel">
            <h2>📦 Evidence Packaging</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Simulate cryptographic hashing of digital evidence to maintain chain of custody for international courts.
            </p>
            <form onSubmit={handlePackageEvidence}>
              <div className="gj-form-group">
                <label>Evidence ID</label>
                <input type="text" value={evidenceId} onChange={(e) => setEvidenceId(e.target.value)} required />
              </div>
              <div className="gj-form-group">
                <label>Raw Data Payload</label>
                <textarea rows={2} value={rawData} onChange={(e) => setRawData(e.target.value)} required />
              </div>
              <button type="submit" className="gj-btn" disabled={loading} style={{ background: '#b721ff', color: '#fff' }}>Generate SHA-256 Hash</button>
            </form>

            {evidenceResult && (
              <div className="gj-result-box nominal">
                <div className="gj-result-title" style={{ color: '#00ffcc' }}>EVIDENCE SECURED</div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem', wordBreak: 'break-all' }}>
                  <strong>Hash: </strong> {evidenceResult.file_hash}
                  <br />
                  <span style={{ color: '#888' }}>{evidenceResult.encryption_standard}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="gj-panel" style={{ marginBottom: '2rem' }}>
            <h2>📜 MLAT Treaty Compliance</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Check Mutual Legal Assistance Treaties to determine processing times for international subpoenas.
            </p>
            <form onSubmit={handleCheckMlat}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="gj-form-group">
                  <label>Requesting Country</label>
                  <input type="text" value={reqCountry} onChange={(e) => setReqCountry(e.target.value)} required />
                </div>
                <div className="gj-form-group">
                  <label>Receiving Country</label>
                  <input type="text" value={recCountry} onChange={(e) => setRecCountry(e.target.value)} required />
                </div>
              </div>
              <button type="submit" className="gj-btn" disabled={loading} style={{ background: '#00ffcc', color: '#000' }}>Check Treaty Status</button>
            </form>

            {mlatResult && (
              <div className={`gj-result-box ${mlatResult.expedited_routing_available ? 'nominal' : (mlatResult.estimated_processing_days > 180 ? 'danger' : 'warning')}`}>
                <div className="gj-result-title" style={{ color: mlatResult.expedited_routing_available ? '#00ffcc' : (mlatResult.estimated_processing_days > 180 ? '#ff4444' : '#ffaa00') }}>
                  {mlatResult.treaty_status.toUpperCase()}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Est. Processing</div>
                    <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{mlatResult.estimated_processing_days} Days</div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Expedited</div>
                    <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{mlatResult.expedited_routing_available ? 'YES' : 'NO'}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="gj-panel">
            <h2>🤝 Inter-Agency Handoff</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Clear an international case and route it to the CollabGuard module for joint agency operational execution.
            </p>
            <form onSubmit={handleLinkModule}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="gj-form-group">
                  <label>Case ID</label>
                  <input type="text" value={linkCaseId} onChange={(e) => setLinkCaseId(e.target.value)} required />
                </div>
                <div className="gj-form-group">
                  <label>Target Agency</label>
                  <select value={agencyCode} onChange={(e) => setAgencyCode(e.target.value)}>
                    <option value="INTERPOL">INTERPOL</option>
                    <option value="EUROPOL">EUROPOL</option>
                    <option value="FBI">FBI Cyber Division</option>
                  </select>
                </div>
              </div>
              <button type="submit" className="gj-btn" disabled={loading} style={{ background: '#333', color: '#ffaa00', border: '1px solid #ffaa00' }}>Route to CollabGuard</button>
            </form>

            {linkResult && (
              <div className="gj-result-box info">
                <div className="gj-result-title" style={{ color: '#4facfe' }}>
                  ✓ ROUTING SUCCESS
                </div>
                <div style={{ color: '#888', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                  {linkResult.status}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
