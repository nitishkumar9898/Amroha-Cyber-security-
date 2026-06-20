import React, { useState } from 'react';
import './MetaGuardDashboard.css';

interface AssetResult {
  asset_id: string;
  is_laundering_risk: boolean;
  action_taken: string;
}

interface AvatarResult {
  avatar_id: string;
  social_engineering_risk: boolean;
  risk_assessment: string;
}

interface CorrelationResult {
  virtual_incident_id: string;
  hardware_id_hash: string;
  physical_location_estimate: string;
}

interface EvidenceResult {
  scene_id: string;
  manifest_url: string;
  is_training_ready: boolean;
}

export default function MetaGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Asset State
  const [assetId, setAssetId] = useState('NFT-LAND-1337');
  const [walletHops, setWalletHops] = useState<number>(6);
  const [timeWindow, setTimeWindow] = useState<number>(45.0);
  const [assetResult, setAssetResult] = useState<AssetResult | null>(null);

  // Avatar State
  const [avatarId, setAvatarId] = useState('USER-X99');
  const [kinematicJitter, setKinematicJitter] = useState<number>(9.5);
  const [manipulativeLanguage, setManipulativeLanguage] = useState<boolean>(true);
  const [avatarResult, setAvatarResult] = useState<AvatarResult | null>(null);

  // Correlation State
  const [incidentId, setIncidentId] = useState('HEIST-001');
  const [ipLog, setIpLog] = useState('192.168.1.1 (TOR NODE)');
  const [correlationResult, setCorrelationResult] = useState<CorrelationResult | null>(null);

  // Evidence State
  const [sceneId, setSceneId] = useState('SCENE-XYZ');
  const [spatialData, setSpatialData] = useState('{...point cloud...}');
  const [evidenceResult, setEvidenceResult] = useState<EvidenceResult | null>(null);

  const handleAssetTrack = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAssetResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/metaguard/track-asset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_id: assetId,
          wallet_hops: walletHops,
          time_window_seconds: timeWindow
        })
      });
      if (!response.ok) throw new Error('Asset tracking failed');
      setAssetResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAvatarResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/metaguard/analyze-avatar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avatar_id: avatarId,
          kinematic_jitter: kinematicJitter,
          manipulative_language: manipulativeLanguage
        })
      });
      if (!response.ok) throw new Error('Avatar analysis failed');
      setAvatarResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCrimeCorrelate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setCorrelationResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/metaguard/correlate-crime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          virtual_incident_id: incidentId,
          virtual_ip_log: ipLog
        })
      });
      if (!response.ok) throw new Error('Crime correlation failed');
      setCorrelationResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEvidenceVisualize = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setEvidenceResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/metaguard/visualize-evidence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scene_id: sceneId,
          raw_spatial_data: spatialData
        })
      });
      if (!response.ok) throw new Error('Evidence visualization failed');
      setEvidenceResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="metaguard-dashboard">
      <header className="mg-header">
        <h1>🥽 MetaGuard Architect</h1>
        <p>Metaverse Forensics, Avatar Behavior, & Immersive Crime Scene Reconstruction</p>
      </header>

      {error && <div className="mg-alert">{error}</div>}

      <div className="mg-grid">
        {/* Left Column */}
        <div>
          <div className="mg-panel" style={{ marginBottom: '2rem' }}>
            <h2>💎 Virtual Asset Tracker</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Detect virtual money laundering by tracking asset transfer velocity across wallets.
            </p>
            <form onSubmit={handleAssetTrack}>
              <div className="mg-form-group">
                <label>Asset ID / Smart Contract</label>
                <input type="text" value={assetId} onChange={(e) => setAssetId(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="mg-form-group">
                  <label>Wallet Hops</label>
                  <input type="number" value={walletHops} onChange={(e) => setWalletHops(parseInt(e.target.value))} required />
                </div>
                <div className="mg-form-group">
                  <label>Time Window (seconds)</label>
                  <input type="number" step="0.1" value={timeWindow} onChange={(e) => setTimeWindow(parseFloat(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="mg-btn" disabled={loading}>Trace Transactions</button>
            </form>

            {assetResult && (
              <div className={`mg-result-box ${assetResult.is_laundering_risk ? 'danger' : 'nominal'}`}>
                <div className="mg-result-title" style={{ color: assetResult.is_laundering_risk ? '#ff4444' : '#00ffcc' }}>
                  {assetResult.is_laundering_risk ? 'LAUNDERING DETECTED' : 'ASSET NOMINAL'}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem' }}>{assetResult.action_taken}</div>
              </div>
            )}
          </div>

          <div className="mg-panel">
            <h2>🌍 Virtual-Real World Correlation</h2>
            <form onSubmit={handleCrimeCorrelate}>
              <div className="mg-form-group">
                <label>Virtual Incident ID</label>
                <input type="text" value={incidentId} onChange={(e) => setIncidentId(e.target.value)} required />
              </div>
              <div className="mg-form-group">
                <label>Virtual IP / Node Log</label>
                <input type="text" value={ipLog} onChange={(e) => setIpLog(e.target.value)} required />
              </div>
              <button type="submit" className="mg-btn" disabled={loading} style={{ background: '#333', color: '#d82bd8', border: '1px solid #d82bd8' }}>Extrapolate Physical ID</button>
            </form>

            {correlationResult && (
              <div className="mg-result-box info">
                <div className="mg-result-title" style={{ color: '#d82bd8' }}>Identity Unmasked</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Hardware Hash</div>
                    <div style={{ fontFamily: 'monospace', color: '#e0e0e0' }}>{correlationResult.hardware_id_hash}</div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Physical Location</div>
                    <div style={{ color: '#e0e0e0' }}>{correlationResult.physical_location_estimate}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="mg-panel" style={{ marginBottom: '2rem' }}>
            <h2>🧍‍♂️ Avatar Behavior Analysis</h2>
            <form onSubmit={handleAvatarAnalyze}>
              <div className="mg-form-group">
                <label>Avatar ID</label>
                <input type="text" value={avatarId} onChange={(e) => setAvatarId(e.target.value)} required />
              </div>
              <div className="mg-form-group">
                <label>Kinematic Jitter (Movement Noise)</label>
                <input type="number" step="0.1" value={kinematicJitter} onChange={(e) => setKinematicJitter(parseFloat(e.target.value))} required />
              </div>
              <div className="mg-form-group" style={{ display: 'flex', alignItems: 'center', marginTop: '1.5rem' }}>
                <input 
                  type="checkbox" 
                  id="nlpCheck"
                  checked={manipulativeLanguage} 
                  onChange={(e) => setManipulativeLanguage(e.target.checked)} 
                />
                <label htmlFor="nlpCheck" style={{ margin: 0, color: '#e0e0e0' }}>Manipulative NLP Signature Detected</label>
              </div>
              <button type="submit" className="mg-btn" disabled={loading} style={{ background: '#ffaa00', color: '#000' }}>Analyze Kinematics & Voice</button>
            </form>

            {avatarResult && (
              <div className={`mg-result-box ${avatarResult.social_engineering_risk ? 'warning' : 'nominal'}`}>
                <div className="mg-result-title" style={{ color: avatarResult.social_engineering_risk ? '#ffaa00' : '#00ffcc' }}>
                  {avatarResult.social_engineering_risk ? 'SOCIAL ENGINEERING RISK' : 'BEHAVIOR NOMINAL'}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem' }}>{avatarResult.risk_assessment}</div>
              </div>
            )}
          </div>

          <div className="mg-panel">
            <h2>🎥 3D Scene Visualization (Training Link)</h2>
            <form onSubmit={handleEvidenceVisualize}>
              <div className="mg-form-group">
                <label>Virtual Scene ID</label>
                <input type="text" value={sceneId} onChange={(e) => setSceneId(e.target.value)} required />
              </div>
              <div className="mg-form-group">
                <label>Raw Spatial Data (Point Cloud)</label>
                <textarea rows={3} value={spatialData} onChange={(e) => setSpatialData(e.target.value)} required />
              </div>
              <button type="submit" className="mg-btn" disabled={loading} style={{ background: '#00ffcc', color: '#000' }}>Generate 3D Manifest</button>
            </form>

            {evidenceResult && (
              <div className="mg-result-box nominal">
                <div className="mg-result-title" style={{ color: '#00ffcc' }}>✓ Training Simulator Ready</div>
                <div style={{ margin: '1rem 0' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Manifest URL</div>
                  <a href={evidenceResult.manifest_url} style={{ color: '#00ffcc', wordBreak: 'break-all' }} onClick={(e) => e.preventDefault()}>
                    {evidenceResult.manifest_url}
                  </a>
                </div>
                <div style={{ color: '#888', fontSize: '0.8rem' }}>* URL mocked for integration with Amroha01 Training module.</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
