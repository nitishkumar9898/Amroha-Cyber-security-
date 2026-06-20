import { useState, useEffect } from 'react';

interface ScenarioRun {
  id: number;
  scenario_id: string;
  name: string;
  threat_actor: string;
  target_sector: string;
  status: string;
  start_time: string;
  completed_phases: string;
}

export const AdminPanel = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [runs, setRuns] = useState<ScenarioRun[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);

  // New scenario run states
  const [newRunName, setNewRunName] = useState('Supply Chain Infiltration');
  const [newRunActor, setNewRunActor] = useState('APT-Shadow-Agent-01');
  const [newRunSector, setNewRunSector] = useState('Defense & Aerospace');

  // Remediation states
  const [remediationSignature, setRemediationSignature] = useState('Ransomware.WannaCry.v2');
  const [remediationLog, setRemediationLog] = useState<any>(null);
  const [healing, setHealing] = useState(false);

  const fetchRuns = async () => {
    if (!token) return;
    setLoadingRuns(true);
    try {
      const res = await fetch('/api/scenario/runs', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
      } else {
        // If 401, token might be expired
        if (res.status === 401) {
          handleLogout();
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchRuns();
    }
  }, [token]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Login failed');
      }

      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setRuns([]);
  };

  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const res = await fetch('/api/scenario/runs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newRunName,
          threat_actor: newRunActor,
          target_sector: newRunSector
        })
      });

      if (res.ok) {
        // Clear name and refresh list
        setNewRunName('Supply Chain Infiltration');
        fetchRuns();
      } else {
        alert('Failed to launch simulation run');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleTriggerRemediation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setHealing(true);
    setRemediationLog(null);

    try {
      const res = await fetch(`/api/remediation/trigger?threat_signature=${encodeURIComponent(remediationSignature)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setRemediationLog(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setHealing(false);
    }
  };

  const autofillCredentials = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
  };

  if (!token) {
    return (
      <section className="animate-in" style={{ padding: '24px 0' }}>
        <div className="dashboard-header">
          <h1 className="section-title">
            <span className="icon">⚙️</span>
            <span className="text-gradient">Forensic Range Admin Login</span>
          </h1>
          <p className="section-subtitle">Provide your credentials to access active simulation and forensic decoders.</p>
        </div>

        <div style={{ maxWidth: '480px', margin: '0 auto' }} className="panel">
          <h3>Authentication Required</h3>
          
          {error && (
            <div className="badge badge-critical" style={{ width: '100%', padding: '10px', borderRadius: '6px', marginBottom: '16px', display: 'block', textAlign: 'center' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} style={{ marginTop: '16px' }}>
            <div className="form-group">
              <label>Username</label>
              <input 
                type="text" 
                className="form-input mono" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input 
                type="password" 
                className="form-input mono" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          <div style={{ marginTop: '24px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, display: 'block', marginBottom: '10px' }}>
              Seeded Test Profiles
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button 
                type="button" 
                className="btn btn-outline btn-sm mono" 
                onClick={() => autofillCredentials('officer_sharma', 'secure_pass_2026')}
                style={{ justifyContent: 'space-between', fontSize: '0.75rem' }}
              >
                <span>👤 Officer Sharma (Investigator)</span>
                <span style={{ opacity: 0.6 }}>Delhi Cyber Unit</span>
              </button>
              <button 
                type="button" 
                className="btn btn-outline btn-sm mono" 
                onClick={() => autofillCredentials('director_patel', 'admin_secret_2026')}
                style={{ justifyContent: 'space-between', fontSize: '0.75rem' }}
              >
                <span>👤 Director Patel (Admin)</span>
                <span style={{ opacity: 0.6 }}>NIA HQ</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="animate-in" style={{ padding: '24px 0' }}>
      <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="section-title">
            <span className="icon">⚙️</span>
            <span className="text-gradient">Simulation & Audit Control Center</span>
          </h1>
          <p className="section-subtitle">Create new cyber-warfare scenarios and audit running timeline logs.</p>
        </div>
        <button className="btn btn-danger" onClick={handleLogout}>
          Sign Out
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px', alignItems: 'start' }}>
        
        {/* LAUNCH SIMULATOR FORM */}
        <div className="panel">
          <h3>Deploy Threat Simulator Scenario</h3>
          <form onSubmit={handleCreateRun} style={{ marginTop: '16px' }}>
            <div className="form-group">
              <label>Scenario Name</label>
              <input 
                type="text" 
                className="form-input" 
                value={newRunName} 
                onChange={(e) => setNewRunName(e.target.value)} 
                required
              />
            </div>
            <div className="form-group">
              <label>Threat Actor Group</label>
              <select className="form-select" value={newRunActor} onChange={(e) => setNewRunActor(e.target.value)}>
                <option value="APT-Shadow-Agent-01">APT-Shadow-Agent-01</option>
                <option value="LazarusGroup-IN">LazarusGroup-IN</option>
                <option value="SideWinder-APT">SideWinder-APT</option>
              </select>
            </div>
            <div className="form-group">
              <label>Target Critical Sector</label>
              <select className="form-select" value={newRunSector} onChange={(e) => setNewRunSector(e.target.value)}>
                <option value="Defense & Aerospace">Defense & Aerospace</option>
                <option value="Banking & Finance">Banking & Finance</option>
                <option value="Power Grid Infrastructure">Power Grid Infrastructure</option>
                <option value="Government e-Services">Government e-Services</option>
                <option value="Telecom Networks">Telecom Networks</option>
                <option value="Healthcare Systems">Healthcare Systems</option>
              </select>
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
              🚀 Initialize Simulator Range
            </button>
          </form>
        </div>

        {/* ACTIVE SIMULATIONS LIST */}
        <div className="panel" style={{ minHeight: '380px' }}>
          <h3>Active Simulator Nodes</h3>
          
          {loadingRuns ? (
            <div className="loading-spinner" style={{ height: '240px' }}>
              <div className="spinner"></div>
              <span>Connecting to range controller database...</span>
            </div>
          ) : runs.length === 0 ? (
            <div className="empty-state" style={{ height: '240px' }}>
              <p>No simulator runs currently registered in SQLite database.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto', marginTop: '12px' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Scenario ID</th>
                    <th>Name</th>
                    <th>Actor</th>
                    <th>Target Sector</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id}>
                      <td className="mono" style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>{run.scenario_id}</td>
                      <td style={{ fontSize: '0.85rem' }}>{run.name}</td>
                      <td className="mono" style={{ fontSize: '0.8rem' }}>{run.threat_actor}</td>
                      <td style={{ fontSize: '0.85rem' }}>{run.target_sector}</td>
                      <td>
                        <span className={`badge ${run.status === 'COMPLETED' ? 'badge-success' : 'badge-warning'}`}>
                          {run.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* AUTO REMEDIATION PANEL */}
      <div className="panel" style={{ marginTop: '24px' }}>
        <h3>Autonomous Self-Healing & Remediation</h3>
        <p className="section-subtitle" style={{ marginBottom: '16px' }}>
          Trigger SentinelCore's active response agents to dynamically rewrite firewall rules, isolate nodes, and inject adversarial noise.
        </p>
        
        <form onSubmit={handleTriggerRemediation} style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', marginBottom: '20px' }}>
          <div className="form-group" style={{ flexGrow: 1, marginBottom: 0 }}>
            <label>Threat Signature Target</label>
            <input 
              type="text" 
              className="form-input mono" 
              value={remediationSignature} 
              onChange={(e) => setRemediationSignature(e.target.value)} 
              required
            />
          </div>
          <button type="submit" className="btn btn-danger" disabled={healing}>
            {healing ? 'Initiating Countermeasures...' : 'Trigger Auto-Remediation'}
          </button>
        </form>

        {remediationLog && (
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', borderLeft: '4px solid var(--primary-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span className="badge badge-success">STATUS: {remediationLog.status}</span>
              <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{remediationLog.timestamp}</span>
            </div>
            <ul style={{ listStyleType: 'none', margin: 0, padding: 0 }}>
              {remediationLog.actions.map((action: string, idx: number) => (
                <li key={idx} style={{ padding: '8px 0', borderBottom: idx !== remediationLog.actions.length - 1 ? '1px solid var(--border)' : 'none', color: 'var(--accent-cyan)', fontSize: '0.9rem' }}>
                  <span style={{ marginRight: '8px' }}>⚡</span> {action}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

    </section>
  );
};
