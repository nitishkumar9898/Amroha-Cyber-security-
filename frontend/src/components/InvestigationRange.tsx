import { useState } from 'react';

export const InvestigationRange = () => {
  const [loading, setLoading] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState<string>('// Initialize a forensic scanner from the control panel...\n// Awaiting secure payload request.');
  const token = localStorage.getItem('token');

  // Input states
  const [deepfakePath, setDeepfakePath] = useState('media_evidence/fake_video.mp4');
  const [malwareName, setMalwareName] = useState('suspicious_installer.exe');
  const [mobileDbPath, setMobileDbPath] = useState('forensic_evidence/chat_history.db');
  const [darkwebPath, setDarkwebPath] = useState('scraped_data/intel_post.json');
  const [psychologyText, setPsychologyText] = useState('Urgent: Deposit 5 BTC or critical assets will be liquidated.');
  const [behavioralUserId, setBehavioralUserId] = useState('');
  const [behavioralFootprint, setBehavioralFootprint] = useState('{\"messages\": [], \"activities\": []}');
  const [behavioralActivities, setBehavioralActivities] = useState('[]');
  const [claimText, setClaimText] = useState('Breaking: Defense servers hit by zero-day outage.');
  const [hardwareVid, setHardwareVid] = useState('0x046d');
  const [hardwarePid, setHardwarePid] = useState('0xc52b');
  const [hardwareSerial, setHardwareSerial] = useState('USB_DUCKY_123');

  const executeForensic = async (endpoint: string, method: string = 'GET', body: any = null, moduleName: string) => {
    setLoading(true);
    setConsoleOutput(`[SYSTEM] Initializing forensic target: ${moduleName.toUpperCase()}...\n[CONNECT] Requesting ${method} ${endpoint}...`);

    try {
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      if (body) {
        headers['Content-Type'] = 'application/json';
      }

      const options: RequestInit = {
        method,
        headers,
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      const res = await fetch(endpoint, options);
      if (res.status === 401) {
        setConsoleOutput('[ERROR 401] Unauthorized. Please log in through the Admin Panel first.');
        return;
      }
      
      const data = await res.json();
      setConsoleOutput(`[SUCCESS] Forensic extraction complete.\n\n${JSON.stringify(data, null, 2)}`);
    } catch (err: any) {
      setConsoleOutput(`[FAILURE] Connection error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTamper = async () => {
    await executeForensic('/api/forensics/tamper', 'POST', null, 'Tamper Evidence');
  };

  const handleVerify = async () => {
    await executeForensic(`/api/forensics/verify?filepath=${encodeURIComponent(mobileDbPath)}`, 'POST', null, 'Hash Integrity Audit');
  };

  const handleCertify = async () => {
    await executeForensic('/api/forensics/certify', 'POST', {
      filepath: mobileDbPath,
      examiner_designation: 'Cyber Crime Examiner'
    }, 'BSA Certify');
  };

  return (
    <section className="animate-in" style={{ padding: '24px 0' }}>
      <div className="dashboard-header">
        <h1 className="section-title">
          <span className="icon">🔬</span>
          <span className="text-gradient">Forensic Investigation Range</span>
        </h1>
        <p className="section-subtitle">Simulate multi-channel threat vector extraction and verify integrity markers.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px', alignItems: 'start' }}>
        
        {/* SCANNERS CONTROL PANEL */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* DEEPFAKE */}
          <div className="panel" style={{ padding: '16px' }}>
            <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>📹 Deepfake Media Scanner</h4>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input 
                type="text" 
                className="form-input" 
                value={deepfakePath} 
                onChange={(e) => setDeepfakePath(e.target.value)} 
                style={{ fontSize: '0.8rem' }}
              />
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => executeForensic(`/api/forensics/deepfake?filepath=${encodeURIComponent(deepfakePath)}`, 'GET', null, 'Deepfake Detector')}
                disabled={loading}
              >
                Scan
              </button>
            </div>
          </div>

          {/* MALWARE */}
          <div className="panel" style={{ padding: '16px' }}>
            <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>☣️ Malware Sandbox</h4>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input 
                type="text" 
                className="form-input" 
                value={malwareName} 
                onChange={(e) => setMalwareName(e.target.value)} 
                style={{ fontSize: '0.8rem' }}
              />
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => executeForensic(`/api/forensics/malware?binary_name=${encodeURIComponent(malwareName)}`, 'GET', null, 'Malware Sandbox')}
                disabled={loading}
              >
                Simulate
              </button>
            </div>
          </div>

          {/* MOBILE */}
          <div className="panel" style={{ padding: '16px' }}>
            <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>📱 Mobile SQLite Parser</h4>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input 
                type="text" 
                className="form-input" 
                value={mobileDbPath} 
                onChange={(e) => setMobileDbPath(e.target.value)} 
                style={{ fontSize: '0.8rem' }}
              />
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => executeForensic(`/api/forensics/mobile?db_filepath=${encodeURIComponent(mobileDbPath)}`, 'GET', null, 'Mobile Extractor')}
                disabled={loading}
              >
                Parse
              </button>
            </div>
          </div>

          {/* DARKWEB */}
          <div className="panel" style={{ padding: '16px' }}>
            <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>🧅 Dark Web Intel Harvester</h4>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input 
                type="text" 
                className="form-input" 
                value={darkwebPath} 
                onChange={(e) => setDarkwebPath(e.target.value)} 
                style={{ fontSize: '0.8rem' }}
              />
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => executeForensic(`/api/forensics/darkweb?filepath=${encodeURIComponent(darkwebPath)}`, 'GET', null, 'Darkweb Intel')}
                disabled={loading}
              >
                Harvest
              </button>
            </div>
          </div>

          {/* PSYCHOLOGY / MISINFO */}
          <div className="panel" style={{ padding: '16px' }}>
            <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>🧠 Cognitive Analytics & NLP</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input 
                  type="text" 
                  className="form-input" 
                  value={psychologyText} 
                  placeholder="Psychology Text Sample"
                  onChange={(e) => setPsychologyText(e.target.value)} 
                  style={{ fontSize: '0.8rem' }}
                />
                <button 
                  className="btn btn-primary btn-sm"
                  onClick={() => executeForensic(`/api/forensics/psychology?text_sample=${encodeURIComponent(psychologyText)}`, 'POST', null, 'Cyber Psychology')}
                  disabled={loading}
                >
                  Profile
                </button>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input 
                  type="text" 
                  className="form-input" 
                  value={claimText} 
                  placeholder="Misinformation Claim Text"
                  onChange={(e) => setClaimText(e.target.value)} 
                  style={{ fontSize: '0.8rem' }}
                />
                <button 
                  className="btn btn-primary btn-sm"
                  onClick={() => executeForensic(`/api/forensics/misinformation?claim_text=${encodeURIComponent(claimText)}`, 'POST', null, 'Misinfo Checker')}
                  disabled={loading}
                >
                  Verify
                </button>
              </div>
            </div>
          </div>

          {/* BEHAVIORAL PROFILING */}
<div className="panel" style={{ padding: '16px' }}>
  <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>🧠 Behavioral Profiling</h4>
  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
    <input type="text" className="form-input" placeholder="User ID" value={behavioralUserId}
      onChange={(e) => setBehavioralUserId(e.target.value)} style={{ fontSize: '0.8rem' }} />
    <textarea className="form-input" placeholder="Footprint JSON" value={behavioralFootprint}
      onChange={(e) => setBehavioralFootprint(e.target.value)} rows={6}
      style={{ fontSize: '0.8rem' }} />
    <button className="btn btn-primary btn-sm"
      onClick={() => {
        const body = JSON.parse(behavioralFootprint);
        executeForensic(`/api/behavioral/profile/${encodeURIComponent(behavioralUserId)}`, 'POST', body, 'Behavioral Profile');
      }} disabled={loading}>Generate Profile</button>
    <button className="btn btn-primary btn-sm"
      onClick={() => {
        const body = JSON.parse(behavioralFootprint);
        executeForensic('/api/behavioral/scan', 'POST', body, 'Behavioral Scan');
      }} disabled={loading}>Quick Scan</button>
    <textarea className="form-input" placeholder="Activities JSON (list of objects)" value={behavioralActivities}
      onChange={(e) => setBehavioralActivities(e.target.value)} rows={4}
      style={{ fontSize: '0.8rem' }} />
    <button className="btn btn-primary btn-sm"
      onClick={() => {
        const acts = JSON.parse(behavioralActivities);
        executeForensic(`/api/behavioral/insider/${encodeURIComponent(behavioralUserId)}`, 'POST', acts, 'Insider Threat');
      }} disabled={loading}>Predict Insider Threat</button>
  </div>
</div>

{/* HARDWARE */}
          <div className="panel" style={{ padding: '16px' }}>
            <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>🔌 Hardware USB Compliancy</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '8px', alignItems: 'center' }}>
              <input type="text" className="form-input" value={hardwareVid} placeholder="VID" onChange={(e) => setHardwareVid(e.target.value)} style={{ fontSize: '0.8rem' }} />
              <input type="text" className="form-input" value={hardwarePid} placeholder="PID" onChange={(e) => setHardwarePid(e.target.value)} style={{ fontSize: '0.8rem' }} />
              <input type="text" className="form-input" value={hardwareSerial} placeholder="Serial" onChange={(e) => setHardwareSerial(e.target.value)} style={{ fontSize: '0.8rem' }} />
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => executeForensic(`/api/forensics/hardware?vid=${hardwareVid}&pid=${hardwarePid}&serial=${hardwareSerial}`, 'GET', null, 'Hardware Audit')}
                disabled={loading}
              >
                Audit
              </button>
            </div>
          </div>

          {/* AUDIT, TAMPER, CERTIFY (BSA SECTION 63) */}
          <div className="panel" style={{ padding: '20px', background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.05))', borderColor: 'var(--border-glow)' }}>
            <h4 style={{ color: 'var(--accent-purple)', marginBottom: '12px' }}>🔒 BSA Section 63 Evidence Custody & Integrity</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
              <button className="btn btn-danger btn-sm" onClick={handleTamper} disabled={loading}>
                💥 Tamper File
              </button>
              <button className="btn btn-outline btn-sm" onClick={handleVerify} disabled={loading}>
                🔍 Verify Integrity
              </button>
              <button className="btn btn-primary btn-sm" onClick={handleCertify} disabled={loading}>
                📜 Sign BSA Certificate
              </button>
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px' }}>
              * 'Tamper' appends null bytes to the active chat SQLite database, modifying the SHA-256 footprint. Verify Integrity scans for hash mismatch.
            </p>
          </div>

        </div>

        {/* LOG CONSOLE TERMINAL */}
        <div className="panel" style={{ padding: '20px', height: '100%', minHeight: '650px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: loading ? 'var(--accent-amber)' : 'var(--accent-green)' }}></span>
              Forensic Log Output
            </h4>
            <button 
              className="btn btn-outline btn-sm"
              onClick={() => {
                navigator.clipboard.writeText(consoleOutput);
              }}
              style={{ fontSize: '0.75rem', padding: '4px 10px' }}
            >
              Copy Log
            </button>
          </div>
          <textarea
            className="result-block"
            value={consoleOutput}
            readOnly
            style={{ 
              flexGrow: 1, 
              background: '#040711', 
              color: '#38bdf8', 
              border: '1px solid rgba(56, 189, 248, 0.15)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.78rem',
              padding: '12px',
              borderRadius: '6px',
              outline: 'none',
              resize: 'none',
              height: '560px'
            }}
          />
        </div>

      </div>
    </section>
  );
};
