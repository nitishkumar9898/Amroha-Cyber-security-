import React, { useState } from 'react';
import './InnovateGuardDashboard.css';

interface IdeaResult {
  research_data_id: string;
  detected_topic: string;
  novelty_score: number;
  generated_claim: string;
}

interface TheftResult {
  user_id: string;
  is_exfiltration_risk: boolean;
  action_taken: string;
}

interface TrackResult {
  project_name: string;
  current_stage: string;
  message: string;
}

export default function InnovateGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Idea State
  const [researchId, setResearchId] = useState('RES-2026-001');
  const [researchText, setResearchText] = useState('We have developed a novel algorithm for a quantum-resistant sub-molecular sensor.');
  const [ideaResult, setIdeaResult] = useState<IdeaResult | null>(null);

  // Theft State
  const [userId, setUserId] = useState('DEV-088');
  const [dataVolume, setDataVolume] = useState<number>(12.5);
  const [timeAccess, setTimeAccess] = useState('NON_BUSINESS');
  const [theftResult, setTheftResult] = useState<TheftResult | null>(null);

  // Track State
  const [projectName, setProjectName] = useState('Project Apollo');
  const [ownerId, setOwnerId] = useState('RESEARCH-LEAD');
  const [currentStage, setCurrentStage] = useState('PATENT_PENDING');
  const [trackResult, setTrackResult] = useState<TrackResult | null>(null);

  const handleIdeaDetect = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setIdeaResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/innovateguard/detect-idea', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          research_data_id: researchId,
          research_text: researchText
        })
      });
      if (!response.ok) throw new Error('Idea detection failed');
      setIdeaResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTheftInvestigate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTheftResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/innovateguard/investigate-theft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          data_volume_gb: dataVolume,
          time_of_access: timeAccess
        })
      });
      if (!response.ok) throw new Error('Theft investigation failed');
      setTheftResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTrackUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTrackResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/innovateguard/track-innovation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName,
          owner_id: ownerId,
          current_stage: currentStage
        })
      });
      if (!response.ok) throw new Error('Tracking update failed');
      setTrackResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="innovateguard-dashboard">
      <header className="ig-header">
        <h1>💡 InnovateGuard Architect</h1>
        <p>Intellectual Property Protection & Autonomous Patent Detection</p>
      </header>

      {error && <div className="ig-alert">{error}</div>}

      <div className="ig-grid">
        {/* Left Column */}
        <div>
          <div className="ig-panel" style={{ marginBottom: '2rem' }}>
            <h2>🧠 Autonomous Patent Idea Detector</h2>
            <form onSubmit={handleIdeaDetect}>
              <div className="ig-form-group">
                <label>Research Data ID</label>
                <input type="text" value={researchId} onChange={(e) => setResearchId(e.target.value)} required />
              </div>
              <div className="ig-form-group">
                <label>Raw Research Abstract / Methodology</label>
                <textarea rows={4} value={researchText} onChange={(e) => setResearchText(e.target.value)} required />
              </div>
              <button type="submit" className="ig-btn" disabled={loading}>Detect Patentable Claims</button>
            </form>

            {ideaResult && (
              <div className="ig-idea-result">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Novelty Score</div>
                    <div style={{ color: '#ffaa00', fontWeight: 'bold', fontSize: '1.5rem' }}>
                      {ideaResult.novelty_score.toFixed(1)} / 100
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Detected Topic</div>
                    <div style={{ color: '#fff', fontSize: '0.9rem', marginTop: '0.2rem' }}>{ideaResult.detected_topic}</div>
                  </div>
                </div>
                <div style={{ borderTop: '1px solid #333', paddingTop: '1rem' }}>
                  <div style={{ color: '#ffaa00', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Generated Claim</div>
                  <div style={{ color: '#e0e0e0', fontStyle: 'italic' }}>"{ideaResult.generated_claim}"</div>
                </div>
              </div>
            )}
          </div>

          <div className="ig-panel">
            <h2>📈 Innovation Lifecycle Tracker</h2>
            <form onSubmit={handleTrackUpdate}>
              <div className="ig-form-group">
                <label>Project Name</label>
                <input type="text" value={projectName} onChange={(e) => setProjectName(e.target.value)} required />
              </div>
              <div className="ig-form-group">
                <label>Owner ID</label>
                <input type="text" value={ownerId} onChange={(e) => setOwnerId(e.target.value)} required />
              </div>
              <div className="ig-form-group">
                <label>Lifecycle Stage</label>
                <select value={currentStage} onChange={(e) => setCurrentStage(e.target.value)}>
                  <option value="RAW_RESEARCH">RAW_RESEARCH</option>
                  <option value="PATENT_PENDING">PATENT_PENDING</option>
                  <option value="SECURED">SECURED</option>
                </select>
              </div>
              <button type="submit" className="ig-btn" disabled={loading} style={{ background: '#333', color: '#fff', border: '1px solid #ffaa00' }}>Update Track</button>
            </form>

            {trackResult && (
              <div className="ig-track-result">
                <div style={{ color: '#ffaa00', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {trackResult.current_stage}
                </div>
                <div style={{ color: '#e0e0e0' }}>{trackResult.message}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="ig-panel">
            <h2>🕵️‍♂️ IP Exfiltration Heuristic</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Analyze access logs to detect anomalous downloads of proprietary research data.
            </p>
            <form onSubmit={handleTheftInvestigate}>
              <div className="ig-form-group">
                <label>User ID</label>
                <input type="text" value={userId} onChange={(e) => setUserId(e.target.value)} required />
              </div>
              <div className="ig-form-group">
                <label>Data Volume Downloaded (GB)</label>
                <input type="number" step="0.1" value={dataVolume} onChange={(e) => setDataVolume(parseFloat(e.target.value))} required />
              </div>
              <div className="ig-form-group">
                <label>Time of Access</label>
                <select value={timeAccess} onChange={(e) => setTimeAccess(e.target.value)}>
                  <option value="BUSINESS_HOURS">Business Hours</option>
                  <option value="NON_BUSINESS">Non-Business Hours</option>
                </select>
              </div>
              <button type="submit" className="ig-btn" disabled={loading} style={{ background: '#ff4444', color: '#fff' }}>Run Theft Heuristic</button>
            </form>

            {theftResult && (
              <div className={`ig-theft-result ${theftResult.is_exfiltration_risk ? 'risk' : 'safe'}`}>
                <div style={{ fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  {theftResult.is_exfiltration_risk ? 'EXFILTRATION RISK' : 'ACCESS NOMINAL'}
                </div>
                <div style={{ color: '#e0e0e0' }}>{theftResult.action_taken}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
