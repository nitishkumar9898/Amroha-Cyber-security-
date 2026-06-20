import React, { useState, useEffect } from "react";
import axios from "axios";
import "./PsyOpsForgeDashboard.css";

export const PsyOpsForgeDashboard: React.FC = () => {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [target, setTarget] = useState("");
  const [misinfoType, setMisinfoType] = useState("");
  const [strategy, setStrategy] = useState<any>(null);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = () => {
    axios.get("/api/psyopsforge/campaigns").then(res => setCampaigns(res.data)).catch(console.error);
  };

  const handleSimulate = () => {
    axios.post("/api/psyopsforge/campaigns", { target_demographic: target, misinformation_type: misinfoType })
      .then(() => {
        fetchCampaigns();
        setTarget(""); setMisinfoType("");
      })
      .catch(console.error);
  };

  const handleCounter = (id: number) => {
    axios.get(`/api/psyopsforge/campaigns/${id}/counter`)
      .then(res => setStrategy(res.data))
      .catch(console.error);
  };

  return (
    <div className="po-container">
      <h2>PsyOpsForge Dashboard</h2>
      
      <div className="po-card">
        <h3>Simulate Influence Campaign</h3>
        <input placeholder="Target Demographic" value={target} onChange={e => setTarget(e.target.value)} />
        <input placeholder="Misinformation Type (e.g., Deepfake)" value={misinfoType} onChange={e => setMisinfoType(e.target.value)} />
        <button onClick={handleSimulate}>Run Simulation</button>
      </div>

      {strategy && (
        <div className="po-card po-strategy">
          <h3>Counter-Strategy Generated</h3>
          <p><strong>Strategy:</strong> {strategy.strategy}</p>
          <p><strong>Predicted Recovery:</strong> {(strategy.predicted_recovery * 100).toFixed(1)}%</p>
          <button onClick={() => setStrategy(null)}>Dismiss</button>
        </div>
      )}

      <div className="po-card">
        <h3>Active Campaign Simulations</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Target</th>
              <th>Type</th>
              <th>Impact</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map(camp => (
              <tr key={camp.id}>
                <td>{camp.id}</td>
                <td>{camp.target_demographic}</td>
                <td>{camp.misinformation_type}</td>
                <td>{(camp.sentiment_impact * 100).toFixed(1)}% Negative</td>
                <td>{camp.status}</td>
                <td>
                  <button className="counter-btn" onClick={() => handleCounter(camp.id)}>Counter-Ops</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
