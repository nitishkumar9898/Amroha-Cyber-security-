import React, { useState } from 'react';
import './CampaignGuardDashboard.css';
import { NetworkChart } from './NetworkChart';

export const CampaignGuardDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [mediaUrl, setMediaUrl] = useState('https://fake-media-hub.io/v/123991.mp4');
  const [targetEntity, setTargetEntity] = useState('Elections2028');

  const [results, setResults] = useState<any>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/campaignguard/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_url: mediaUrl, target_entity: targetEntity })
      });
      if (!res.ok) throw new Error('Failed to analyze deepfake campaign');
      const data = await res.json();
      
      // Build Graph Data
      const nodes: any[] = [];
      const links: any[] = [];
      
      // Add a central node for the payload
      nodes.push({ id: 'Payload', label: `Payload\n${data.campaign.payload_hash.substring(0,6)}`, type: 'infrastructure' });

      // Add bots
      data.bot_nodes.forEach((bot: any) => {
        let nodeType = 'target';
        if (bot.node_type === 'origin') nodeType = 'actor';
        if (bot.node_type === 'bridge') nodeType = 'infrastructure';
        
        nodes.push({ id: bot.node_id, label: `${bot.node_type}\n${bot.platform}`, type: nodeType });
        
        if (bot.node_type === 'origin') {
          links.push({ source: 'Payload', target: bot.node_id, relationship: 'SEEDED' });
        } else if (bot.node_type === 'amplifier') {
          // Find an origin of the same platform to link to
          const origin = data.bot_nodes.find((b: any) => b.node_type === 'origin' && b.platform === bot.platform);
          if (origin) {
            links.push({ source: origin.node_id, target: bot.node_id, relationship: 'AMPLIFIED_BY' });
          } else {
             links.push({ source: 'Payload', target: bot.node_id, relationship: 'AMPLIFIED' });
          }
        } else if (bot.node_type === 'bridge') {
           links.push({ source: 'Payload', target: bot.node_id, relationship: 'BRIDGED' });
        }
      });

      setResults({
        ...data,
        graphData: { actor: 'Op-Campaign', nodes, links }
      });

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="campaignguard-dashboard">
      <div className="campaignguard-header">
        <h2>CampaignGuard</h2>
        <p>Deepfake Tracking & Influence Operation Analysis</p>
      </div>

      <div className="campaignguard-controls">
        <form onSubmit={handleAnalyze} className="campaignguard-form">
          <div className="form-group">
            <label>Suspected Media URL</label>
            <input type="text" value={mediaUrl} onChange={(e) => setMediaUrl(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Target Entity/Event</label>
            <input type="text" value={targetEntity} onChange={(e) => setTargetEntity(e.target.value)} />
          </div>
          <button type="submit" disabled={loading} className="analyze-btn">
            {loading ? 'Tracing Propagation...' : 'Trace Campaign'}
          </button>
        </form>
        {error && <div className="error-box">{error}</div>}
      </div>

      {results && (
        <div className="campaignguard-results">
          
          <div className="metrics-row">
             <div className="metric-card">
               <h4>Payload Fingerprint</h4>
               <span className="mono-text">{results.campaign.payload_hash}</span>
             </div>
             <div className="metric-card">
               <h4>Affected Platforms</h4>
               <div className="platform-tags">
                 {results.campaign.platforms_affected.map((p: string) => (
                   <span key={p} className="plat-tag">{p}</span>
                 ))}
               </div>
             </div>
             <div className="metric-card">
               <h4>Opinion Impact Score</h4>
               <span className={`impact-score ${(results.impact.impact_score > 0.7) ? 'critical' : 'warning'}`}>
                 {(results.impact.impact_score * 100).toFixed(1)} / 100
               </span>
             </div>
             <div className="metric-card">
               <h4>Estimated Reach</h4>
               <span className="reach-number">{(results.impact.reach_estimate).toLocaleString()} users</span>
             </div>
          </div>

          <div className="visuals-row">
            <div className="cg-panel graph-panel">
              <h3>Bot Swarm Graph Analysis</h3>
              <NetworkChart graphData={results.graphData} />
            </div>
            
            <div className="cg-panel takedown-panel">
              <h3>Automated Takedown Engine</h3>
              <ul className="takedown-list">
                {results.recommendations.map((r: any) => (
                  <li key={r.id} className="takedown-item">
                    <div className="t-header">
                      <span className="t-plat">{r.platform}</span>
                      <span className="t-status">{r.status}</span>
                    </div>
                    <div className="t-body">
                      <strong>Policy:</strong> {r.policy_violation}
                    </div>
                    <div className="t-footer">
                      <p>{r.evidence_summary}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <button className="execute-takedowns-btn">Execute All Takedowns via API</button>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

export default CampaignGuardDashboard;
