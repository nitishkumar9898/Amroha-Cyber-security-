import { useState } from 'react';

export const Reports = () => {
  const [scenarioName, setScenarioName] = useState('APT-Shadow-Agent-01');
  const [threatActor, setThreatActor] = useState('APT-Shadow-Agent-01');
  const [sector, setSector] = useState('Defense & Aerospace');
  const [analystName, setAnalystName] = useState('Officer Sharma');
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const url = `/api/report/generate?scenario_name=${encodeURIComponent(scenarioName)}&threat_actor=${encodeURIComponent(threatActor)}&sector=${encodeURIComponent(sector)}&analyst_name=${encodeURIComponent(analystName)}`;
      const res = await fetch(url, {
        method: 'POST',
        headers,
      });

      if (res.status === 401) {
        alert('Unauthorized. Please log in through the Admin Panel.');
        setLoading(false);
        return;
      }

      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="animate-in" style={{ padding: '24px 0' }}>
      <div className="dashboard-header">
        <h1 className="section-title">
          <span className="icon">📋</span>
          <span className="text-gradient">CERT-IN Incident Reporting Hub</span>
        </h1>
        <p className="section-subtitle">Generate structured compliance incident reports under Section 63 BSA & IT Act mandates.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: report ? '1fr 2.5fr' : '1fr', gap: '24px', alignItems: 'start' }}>
        
        {/* REPORT CONFIGURATION PANEL */}
        <div className="panel">
          <h3>Draft Incident Report</h3>
          <form onSubmit={handleSubmit} style={{ marginTop: '16px' }}>
            <div className="form-group">
              <label>Scenario / Campaign Name</label>
              <input 
                type="text" 
                className="form-input" 
                value={scenarioName} 
                onChange={(e) => setScenarioName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Threat Actor Group</label>
              <select className="form-select" value={threatActor} onChange={(e) => setThreatActor(e.target.value)}>
                <option value="APT-Shadow-Agent-01">APT-Shadow-Agent-01</option>
                <option value="LazarusGroup-IN">LazarusGroup-IN</option>
                <option value="SideWinder-APT">SideWinder-APT</option>
                <option value="Custom Group">Custom Group</option>
              </select>
            </div>
            <div className="form-group">
              <label>Affected Critical Sector</label>
              <select className="form-select" value={sector} onChange={(e) => setSector(e.target.value)}>
                <option value="Defense & Aerospace">Defense & Aerospace</option>
                <option value="Banking & Finance">Banking & Finance</option>
                <option value="Power Grid Infrastructure">Power Grid Infrastructure</option>
                <option value="Government e-Services">Government e-Services</option>
                <option value="Telecom Networks">Telecom Networks</option>
                <option value="Healthcare Systems">Healthcare Systems</option>
              </select>
            </div>
            <div className="form-group">
              <label>Reporting Analyst Name</label>
              <input 
                type="text" 
                className="form-input" 
                value={analystName} 
                onChange={(e) => setAnalystName(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? 'Drafting Report...' : 'Compile Incident Report'}
            </button>
          </form>
        </div>

        {/* PRINTABLE REPORT PREVIEW */}
        {report && (
          <div className="panel report-display">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--accent-cyan)', paddingBottom: '12px', marginBottom: '20px' }}>
              <div>
                <span className="badge badge-critical" style={{ fontSize: '0.65rem', marginBottom: '4px' }}>{report.classification}</span>
                <h3 className="mono" style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>{report.incident_id}</h3>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Generated: {report.report_generated}</span>
                <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>{report.agency}</p>
              </div>
            </div>

            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '12px' }}>{report.title}</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '20px' }}>
              <div style={{ padding: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block' }}>Risk Level</span>
                <span style={{ fontWeight: 700, color: 'var(--accent-red)' }}>{report.severity}</span>
              </div>
              <div style={{ padding: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block' }}>Sector Targeted</span>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{report.affected_sector}</span>
              </div>
              <div style={{ padding: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block' }}>Threat Origin</span>
                <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-purple)' }}>{report.threat_actor}</span>
              </div>
            </div>

            <div className="report-section">
              <h4>EXECUTIVE SUMMARY</h4>
              <p style={{ fontSize: '0.85rem' }}>{report.summary}</p>
            </div>

            <div className="report-section">
              <h4>INTRUSION PHASE TIMELINE (MITRE ATT&CK Mapping)</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {report.attack_phases.map((phase: any, index: number) => (
                  <div key={index} className="phase-item">
                    <div className="phase-number">{phase.phase}</div>
                    <div className="phase-details">
                      <h5>{phase.name}</h5>
                      <p>{phase.technique} — <code style={{ fontSize: '0.7rem' }}>{phase.mitre}</code></p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="report-section">
              <h4>INDICATORS OF COMPROMISE (IOCs)</h4>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {report.iocs.map((ioc: any, index: number) => (
                  <div key={index} className="ioc-item">
                    <span className="ioc-type">{ioc.type}</span>
                    <span className="ioc-value">{ioc.value}</span>
                    <span className="badge badge-info" style={{ fontSize: '0.55rem', marginLeft: 'auto' }}>Confidence: {ioc.confidence}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="report-section">
              <h4>RECOMMENDED REMEDIATION ACTIONS</h4>
              <div>
                {report.recommendations.map((rec: string, index: number) => (
                  <div key={index} className="recommendation-item">
                    {rec}
                  </div>
                ))}
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px', marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <strong>Mandatory Reference:</strong> {report.legal_reference}
              </span>
              <button 
                className="btn btn-outline btn-sm"
                onClick={() => window.print()}
                style={{ padding: '6px 14px', fontSize: '0.75rem' }}
              >
                🖨️ Export PDF
              </button>
            </div>
          </div>
        )}

      </div>
    </section>
  );
};
