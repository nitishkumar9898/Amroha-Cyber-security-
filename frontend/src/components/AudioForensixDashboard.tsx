import React, { useState } from 'react';
import './AudioForensixDashboard.css';

interface DeepfakeResult {
  sample_id: string;
  claimed_identity: string;
  match_confidence: number;
  liveness_score: number;
  is_spoofed: boolean;
  high_freq_artifacts: number;
  ai_probability: number;
  is_deepfake: boolean;
}

interface EnvResult {
  sample_id: string;
  rt60_decay: number;
  background_noise_profile: string;
  estimated_environment: string;
}

const AudioForensixDashboard: React.FC = () => {
  const [sampleId, setSampleId] = useState<string>('CALL-INTERCEPT-990');
  const [identity, setIdentity] = useState<string>('Target_Alpha');
  
  const [deepfakeResult, setDeepfakeResult] = useState<DeepfakeResult | null>(null);
  const [envResult, setEnvResult] = useState<EnvResult | null>(null);
  
  const [loadingDf, setLoadingDf] = useState(false);
  const [loadingEnv, setLoadingEnv] = useState(false);

  const analyzeDeepfake = async () => {
    setLoadingDf(true);
    try {
      const res = await fetch('/api/audioforensix/detect-deepfake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_id: sampleId,
          claimed_identity: identity
        })
      });
      const data = await res.json();
      setDeepfakeResult(data);
    } catch (error) {
      console.error(error);
    }
    setLoadingDf(false);
  };

  const reconstructEnvironment = async () => {
    setLoadingEnv(true);
    try {
      const res = await fetch('/api/audioforensix/reconstruct-environment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_id: sampleId
        })
      });
      const data = await res.json();
      setEnvResult(data);
    } catch (error) {
      console.error(error);
    }
    setLoadingEnv(false);
  };

  return (
    <div className="audioforensix-dashboard">
      <div className="dashboard-header">
        <h1>AudioForensix Engine</h1>
        <p>Acoustic Intelligence, Voice Biometrics, & Deepfake Detection</p>
      </div>

      <div className="dashboard-grid">
        {/* Deepfake & Biometrics Panel */}
        <div className="panel">
          <h2>Voice Cloning Detection</h2>
          <div className="input-group">
            <input 
              type="text" 
              value={sampleId} 
              onChange={(e) => setSampleId(e.target.value)} 
              placeholder="Sample ID"
            />
            <input 
              type="text" 
              value={identity} 
              onChange={(e) => setIdentity(e.target.value)} 
              placeholder="Claimed Identity"
            />
            <button className="action-btn" onClick={analyzeDeepfake} disabled={loadingDf}>
              {loadingDf ? "Analyzing Spectrograms..." : "Run Deepfake Analysis"}
            </button>
          </div>

          {deepfakeResult && (
            <div className="result-card">
              <h3>Analysis Results</h3>
              <div className="metric-row">
                <span className="metric-label">Match Confidence:</span>
                <span className="metric-value">{deepfakeResult.match_confidence.toFixed(2)}%</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Liveness Score (Anti-Spoof):</span>
                <span className={`metric-value ${deepfakeResult.liveness_score < 60 ? 'danger' : 'safe'}`}>
                  {deepfakeResult.liveness_score.toFixed(2)} / 100
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">High-Frequency Artifacts:</span>
                <span className="metric-value">{deepfakeResult.high_freq_artifacts.toFixed(2)}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">AI Deepfake Probability:</span>
                <span className={`metric-value ${deepfakeResult.ai_probability > 65 ? 'danger' : 'safe'}`}>
                  {deepfakeResult.ai_probability.toFixed(2)}%
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Final Verdict:</span>
                <span className={`metric-value ${deepfakeResult.is_deepfake ? 'danger' : 'safe'}`}>
                  {deepfakeResult.is_deepfake ? 'SYNTHETIC CLONE DETECTED' : 'AUTHENTIC VOICE'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Environment Reconstruction Panel */}
        <div className="panel">
          <h2>Acoustic Reconstruction</h2>
          <p style={{color: '#a0a0a0', marginBottom: '15px'}}>Analyze reverberation decay and noise profiles to locate the physical recording environment.</p>
          <div className="input-group">
            <button className="action-btn" onClick={reconstructEnvironment} disabled={loadingEnv}>
              {loadingEnv ? "Isolating Acoustics..." : "Reconstruct Environment"}
            </button>
          </div>

          {envResult && (
            <div className="result-card" style={{borderLeftColor: '#ff00cc'}}>
              <h3>Acoustic Signature</h3>
              <div className="metric-row">
                <span className="metric-label">RT60 Reverb Decay:</span>
                <span className="metric-value">{envResult.rt60_decay.toFixed(3)} s</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Background Noise:</span>
                <span className="metric-value">{envResult.background_noise_profile}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Estimated Location:</span>
                <span className="metric-value" style={{color: '#ff00cc'}}>{envResult.estimated_environment}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AudioForensixDashboard;
