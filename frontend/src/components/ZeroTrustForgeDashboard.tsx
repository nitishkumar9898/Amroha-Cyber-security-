import React, { useState } from 'react';
import './ZeroTrustForgeDashboard.css';

interface AuthResult {
  user_id: string;
  trust_score: number;
  context_anomalies: number;
  auth_status: string;
}

interface SegmentResult {
  source_segment: string;
  target_segment: string;
  is_whitelisted: boolean;
  status: string;
}

interface AccessResult {
  user_id: string;
  resource_id: string;
  access_granted: boolean;
  reason: string;
}

interface PolicyResult {
  target_user: string;
  action_taken: string;
  timestamp: string;
}

export default function ZeroTrustForgeDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auth State
  const [authUserId, setAuthUserId] = useState('USER-999');
  const deviceId = 'DEV-XYZ';
  const [ipAddress, setIpAddress] = useState('192.168.1.100');
  const [isOffHours, setIsOffHours] = useState(false);
  const [isGeoAnomaly, setIsGeoAnomaly] = useState(false);
  const [authResult, setAuthResult] = useState<AuthResult | null>(null);

  // Segment State
  const [sourceSeg, setSourceSeg] = useState('HR_VLAN');
  const [targetSeg, setTargetSeg] = useState('FINANCE_DB');
  const [isWhitelisted, setIsWhitelisted] = useState(false);
  const [segmentResult, setSegmentResult] = useState<SegmentResult | null>(null);

  // Access State
  const [accUserId, setAccUserId] = useState('USER-999');
  const [resourceId, setResourceId] = useState('SERVER-1');
  const [userScore, setUserScore] = useState(45.0);
  const [reqScore, setReqScore] = useState(80.0);
  const [accessResult, setAccessResult] = useState<AccessResult | null>(null);

  // Policy State
  const [triggerEvent, setTriggerEvent] = useState('MULTIPLE_FAILED_LOGINS');
  const [polUserId, setPolUserId] = useState('USER-999');
  const [polScore, setPolScore] = useState(45.0);
  const [policyResult, setPolicyResult] = useState<PolicyResult | null>(null);

  const handleAuthenticate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAuthResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/zerotrustforge/authenticate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: authUserId,
          device_id: deviceId,
          ip_address: ipAddress,
          is_off_hours: isOffHours,
          geo_location_anomaly: isGeoAnomaly
        })
      });
      if (!response.ok) throw new Error('Authentication failed');
      setAuthResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSegment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSegmentResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/zerotrustforge/create-segment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_segment: sourceSeg,
          target_segment: targetSeg,
          is_whitelisted: isWhitelisted
        })
      });
      if (!response.ok) throw new Error('Segmentation failed');
      setSegmentResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAccessResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/zerotrustforge/evaluate-access', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: accUserId,
          resource_id: resourceId,
          user_trust_score: userScore,
          required_trust_score: reqScore
        })
      });
      if (!response.ok) throw new Error('Access evaluation failed');
      setAccessResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEnforcePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPolicyResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/zerotrustforge/enforce-policy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trigger_event: triggerEvent,
          target_user: polUserId,
          trust_score: polScore
        })
      });
      if (!response.ok) throw new Error('Policy enforcement failed');
      setPolicyResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="zerotrustforge-dashboard">
      <header className="zt-header">
        <h1>🔐 ZeroTrustForge Architect</h1>
        <p>Continuous Authentication, Micro-Segmentation & Least Privilege</p>
      </header>

      {error && <div className="zt-alert">{error}</div>}

      <div className="zt-grid">
        {/* Left Column */}
        <div>
          <div className="zt-panel" style={{ marginBottom: '2rem' }}>
            <h2>📊 Continuous Authentication</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Evaluate contextual anomalies to generate a dynamic Trust Score for the session.
            </p>
            <form onSubmit={handleAuthenticate}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="zt-form-group">
                  <label>User ID</label>
                  <input type="text" value={authUserId} onChange={(e) => setAuthUserId(e.target.value)} required />
                </div>
                <div className="zt-form-group">
                  <label>IP Address</label>
                  <input type="text" value={ipAddress} onChange={(e) => setIpAddress(e.target.value)} required />
                </div>
              </div>
              <div className="zt-form-group">
                <label className="zt-checkbox">
                  <input type="checkbox" checked={isOffHours} onChange={(e) => setIsOffHours(e.target.checked)} />
                  Off-Hours Access Attempt
                </label>
                <label className="zt-checkbox">
                  <input type="checkbox" checked={isGeoAnomaly} onChange={(e) => setIsGeoAnomaly(e.target.checked)} />
                  Geolocation Anomaly Detected
                </label>
              </div>
              <button type="submit" className="zt-btn" disabled={loading}>Calculate Trust Score</button>
            </form>

            {authResult && (
              <div className={`zt-result-box ${authResult.trust_score < 50 ? 'danger' : (authResult.trust_score < 75 ? 'warning' : 'nominal')}`}>
                <div className="zt-result-title" style={{ color: authResult.trust_score < 50 ? '#ff4444' : (authResult.trust_score < 75 ? '#ffaa00' : '#00ffcc') }}>
                  {authResult.auth_status.toUpperCase()}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                  <div>
                    <span style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Trust Score: </span>
                    <span style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{authResult.trust_score.toFixed(1)} / 100</span>
                  </div>
                  <div>
                    <span style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Anomalies: </span>
                    <span style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{authResult.context_anomalies}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="zt-panel">
            <h2>🚧 Least Privilege Access</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Compare dynamic Trust Score against resource requirements before granting access.
            </p>
            <form onSubmit={handleEvaluateAccess}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="zt-form-group">
                  <label>Resource ID</label>
                  <input type="text" value={resourceId} onChange={(e) => setResourceId(e.target.value)} required />
                </div>
                <div className="zt-form-group">
                  <label>Required Trust Score</label>
                  <input type="number" step="0.1" value={reqScore} onChange={(e) => setReqScore(parseFloat(e.target.value))} required />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="zt-form-group">
                  <label>User ID</label>
                  <input type="text" value={accUserId} onChange={(e) => setAccUserId(e.target.value)} required />
                </div>
                <div className="zt-form-group">
                  <label>Current User Score</label>
                  <input type="number" step="0.1" value={userScore} onChange={(e) => setUserScore(parseFloat(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="zt-btn" disabled={loading} style={{ background: '#b721ff', color: '#fff' }}>Evaluate Access</button>
            </form>

            {accessResult && (
              <div className={`zt-result-box ${accessResult.access_granted ? 'nominal' : 'danger'}`}>
                <div className="zt-result-title" style={{ color: accessResult.access_granted ? '#00ffcc' : '#ff4444' }}>
                  {accessResult.access_granted ? 'ACCESS GRANTED' : 'ACCESS DENIED'}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  {accessResult.reason}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="zt-panel" style={{ marginBottom: '2rem' }}>
            <h2>🛡️ Micro-Segmentation</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Enforce "Default Deny" network isolation between platform segments.
            </p>
            <form onSubmit={handleCreateSegment}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="zt-form-group">
                  <label>Source Segment</label>
                  <input type="text" value={sourceSeg} onChange={(e) => setSourceSeg(e.target.value)} required />
                </div>
                <div className="zt-form-group">
                  <label>Target Segment</label>
                  <input type="text" value={targetSeg} onChange={(e) => setTargetSeg(e.target.value)} required />
                </div>
              </div>
              <div className="zt-form-group">
                <label className="zt-checkbox">
                  <input type="checkbox" checked={isWhitelisted} onChange={(e) => setIsWhitelisted(e.target.checked)} />
                  Route Explicitly Whitelisted
                </label>
              </div>
              <button type="submit" className="zt-btn" disabled={loading} style={{ background: '#ff3366', color: '#fff' }}>Test Communication Route</button>
            </form>

            {segmentResult && (
              <div className={`zt-result-box ${segmentResult.status.includes('BLOCKED') ? 'warning' : 'nominal'}`}>
                <div className="zt-result-title" style={{ color: segmentResult.status.includes('BLOCKED') ? '#ffaa00' : '#00ffcc' }}>
                  {segmentResult.status.includes('BLOCKED') ? 'ROUTE BLOCKED' : 'ROUTE ALLOWED'}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  {segmentResult.status}
                </div>
              </div>
            )}
          </div>

          <div className="zt-panel">
            <h2>⚡ Automated Policy Enforcement</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Trigger automated security responses based on trust degradation or unauthorized access.
            </p>
            <form onSubmit={handleEnforcePolicy}>
              <div className="zt-form-group">
                <label>Trigger Event</label>
                <input type="text" value={triggerEvent} onChange={(e) => setTriggerEvent(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="zt-form-group">
                  <label>Target User ID</label>
                  <input type="text" value={polUserId} onChange={(e) => setPolUserId(e.target.value)} required />
                </div>
                <div className="zt-form-group">
                  <label>Current Trust Score</label>
                  <input type="number" step="0.1" value={polScore} onChange={(e) => setPolScore(parseFloat(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="zt-btn" disabled={loading} style={{ background: '#333', color: '#00ffcc', border: '1px solid #00ffcc' }}>Enforce Policy</button>
            </form>

            {policyResult && (
              <div className="zt-result-box info">
                <div className="zt-result-title" style={{ color: '#4facfe' }}>
                  ✓ ACTION TAKEN
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  <strong>Response:</strong> {policyResult.action_taken}
                  <br />
                  <span style={{ color: '#888', fontSize: '0.8rem' }}>{new Date(policyResult.timestamp).toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
