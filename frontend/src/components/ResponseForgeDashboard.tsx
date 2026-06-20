import React, { useState } from 'react';
import { generatePlaybook, suggestContainment, executeActions } from '../api/responseforge';
import './ResponseForgeDashboard.css';

const ResponseForgeDashboard: React.FC = () => {
  const [incidentType, setIncidentType] = useState('ransomware');
  const [playbook, setPlaybook] = useState<any>(null);
  const [containmentSuggestions, setContainmentSuggestions] = useState<any>(null);
  const [status, setStatus] = useState<string>('');

  const handleGenerate = async () => {
    setStatus('Generating Playbook...');
    const result = await generatePlaybook(incidentType, { urgency: 'high' });
    setPlaybook(result.playbook);
    
    // Auto-fetch containment suggestions for demo
    const suggestions = await suggestContainment({ high_cpu_usage: true });
    setContainmentSuggestions(suggestions.suggestions);
    setStatus('Playbook generated.');
  };

  const handleExecute = async () => {
    if (!containmentSuggestions) return;
    setStatus('Executing containment actions...');
    const res = await executeActions(containmentSuggestions);
    setStatus(`Execution completed: ${res.status}`);
  };

  return (
    <div className="rf-dashboard-container">
      <h1 className="rf-title">ResponseForge Orchestrator</h1>
      <div className="rf-panel">
        <label>Incident Type: </label>
        <select value={incidentType} onChange={(e) => setIncidentType(e.target.value)} className="rf-select">
          <option value="ransomware">Ransomware</option>
          <option value="ddos">DDoS</option>
          <option value="data_breach">Data Breach</option>
        </select>
        <button className="rf-button" onClick={handleGenerate}>Generate Response Plan</button>
      </div>

      {status && <div className="rf-status">{status}</div>}

      <div className="rf-grid">
        <div className="rf-card">
          <h2>AI Playbook</h2>
          {playbook ? (
            <pre className="rf-pre">{JSON.stringify(playbook, null, 2)}</pre>
          ) : (
            <p>No playbook generated yet.</p>
          )}
        </div>

        <div className="rf-card">
          <h2>Containment Advisor</h2>
          {containmentSuggestions ? (
            <div>
              <pre className="rf-pre">{JSON.stringify(containmentSuggestions, null, 2)}</pre>
              <button className="rf-button rf-button-danger" onClick={handleExecute}>Approve & Execute Actions</button>
            </div>
          ) : (
            <p>Awaiting telemetry...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResponseForgeDashboard;
