import React, { useState, useEffect } from "react";
import axios from "axios";
import "./ModelDefenderDashboard.css";

export const ModelDefenderDashboard: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [watermarkModel, setWatermarkModel] = useState("");
  const [watermarkOwner, setWatermarkOwner] = useState("");
  const [watermarkResult, setWatermarkResult] = useState<any>(null);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = () => {
    axios.get("/api/modeldefender/logs").then(res => setLogs(res.data)).catch(console.error);
  };

  const handleWatermark = () => {
    axios.post("/api/modeldefender/watermark", { model_name: watermarkModel, owner_id: watermarkOwner })
      .then(res => setWatermarkResult(res.data))
      .catch(console.error);
  };

  return (
    <div className="md-container">
      <h2>ModelDefender Dashboard</h2>
      
      <div className="md-card">
        <h3>Apply AI Watermark</h3>
        <input placeholder="Model Name" value={watermarkModel} onChange={e => setWatermarkModel(e.target.value)} />
        <input placeholder="Owner ID" value={watermarkOwner} onChange={e => setWatermarkOwner(e.target.value)} />
        <button onClick={handleWatermark}>Generate Watermark</button>
        {watermarkResult && (
          <div className="md-result">
            <p>Hash: {watermarkResult.watermark_hash}</p>
            <p>Status: {watermarkResult.status}</p>
          </div>
        )}
      </div>

      <div className="md-card">
        <h3>Threat Logs</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Model</th>
              <th>Attack Type</th>
              <th>Confidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.model_name}</td>
                <td>{log.attack_type}</td>
                <td>{(log.confidence_score * 100).toFixed(1)}%</td>
                <td>{log.defense_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
