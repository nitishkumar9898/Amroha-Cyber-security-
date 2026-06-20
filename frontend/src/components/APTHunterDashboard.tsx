import React, { useState } from 'react';
import './APTHunterDashboard.css';
import { NetworkChart } from './NetworkChart';

export const APTHunterDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleScanAndMap = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Analyze Persistence
      const mockScanData = {
        scan_data: [
          { type: 'registry', value: 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Malicious' },
          { type: 'wmi', value: 'EventConsumer EvilConsumer' },
          { type: 'scheduled_task', value: 'System Updater' }
        ]
      };

      const persRes = await fetch('http://localhost:8000/api/apthunter/analyze-persistence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockScanData)
      });
      if (!persRes.ok) throw new Error('Failed to analyze persistence');
      const artifacts = await persRes.json();
      const artifactIds = artifacts.map((a: any) => a.id);

      // 2. Map Campaign
      const campRes = await fetch('http://localhost:8000/api/apthunter/map-campaign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ artifact_ids: artifactIds })
      });
      if (!campRes.ok) throw new Error('Failed to map campaign');
      const campaign = await campRes.json();

      // Create Graph Data for Vis Network
      const nodes = [
        { id: 'Actor', label: `Actor: ${campaign.threat_actor_id === 1 ? 'APT29' : 'Unknown'}`, type: 'actor' }
      ];
      const links: any[] = [];

      artifacts.forEach((art: any, i: number) => {
        const artId = `Art_${i}`;
        nodes.push({ id: artId, label: art.artifact_type.toUpperCase(), type: 'target' });
        links.push({ source: 'Actor', target: artId, relationship: 'DEPLOYED' });
        
        // Connect artifacts if they share high stealth score
        if (art.stealth_score > 0.6) {
             nodes.push({ id: `TTP_${i}`, label: 'T1546.003', type: 'infrastructure' });
             links.push({ source: artId, target: `TTP_${i}`, relationship: 'MAPPED_TO' });
        }
      });

      setResults({
        campaignName: campaign.campaign_name,
        confidence: campaign.attribution_confidence,
        graphData: { actor: 'ThreatActor', nodes, links }
      });

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="apthunter-dashboard">
      <div className="apthunter-header">
        <h2>APTHunter Advanced Diagnostics</h2>
        <p>GNN-based TTP Mapping & Campaign Attribution</p>
      </div>

      <div className="apthunter-controls">
        <button 
          className="scan-btn" 
          onClick={handleScanAndMap}
          disabled={loading}
        >
          {loading ? 'Running GNN Analysis...' : 'Initiate Deep System Scan'}
        </button>
      </div>

      {error && <div className="apthunter-error">{error}</div>}

      {results && (
        <div className="apthunter-results-grid">
          <div className="apthunter-card attribution-card">
            <h3>Campaign Attribution</h3>
            <div className="attribution-details">
              <p><strong>Operation Codename:</strong> <span className="highlight">{results.campaignName}</span></p>
              <p><strong>Confidence Score:</strong> <span className="highlight">{(results.confidence * 100).toFixed(1)}%</span></p>
              <div className="confidence-bar">
                <div 
                  className="confidence-fill" 
                  style={{ width: `${results.confidence * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="apthunter-card graph-card">
            <h3>TTP Relational Graph</h3>
            <NetworkChart graphData={results.graphData} />
          </div>
        </div>
      )}
    </div>
  );
};

export default APTHunterDashboard;
