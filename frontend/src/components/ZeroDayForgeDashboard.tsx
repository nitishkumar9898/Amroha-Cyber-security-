import React, { useState, useEffect } from "react";
import axios from "axios";
import "./ZeroDayForgeDashboard.css";

export const ZeroDayForgeDashboard: React.FC = () => {
  const [predictions, setPredictions] = useState<any[]>([]);
  const [component, setComponent] = useState("");
  const [version, setVersion] = useState("");

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = () => {
    axios.get("/api/zerodayforge/predictions").then(res => setPredictions(res.data)).catch(console.error);
  };

  const handlePredict = () => {
    axios.post("/api/zerodayforge/predict", { software_component: component, version })
      .then(() => {
        fetchPredictions();
        setComponent(""); setVersion("");
      })
      .catch(console.error);
  };

  return (
    <div className="zdf-container">
      <h2>ZeroDayForge Dashboard</h2>
      
      <div className="zdf-card">
        <h3>Predict Zero-Day Vulnerability</h3>
        <input placeholder="Software Component (e.g., Linux Kernel)" value={component} onChange={e => setComponent(e.target.value)} />
        <input placeholder="Version (e.g., 6.1.10)" value={version} onChange={e => setVersion(e.target.value)} />
        <button onClick={handlePredict}>Run Prediction</button>
      </div>

      <div className="zdf-card">
        <h3>Vulnerability Predictions</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Component</th>
              <th>Version</th>
              <th>Predicted Severity</th>
              <th>Likely Vulnerability Type</th>
              <th>Prediction Time</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map(pred => (
              <tr key={pred.id}>
                <td>{pred.id}</td>
                <td>{pred.software_component}</td>
                <td>{pred.version}</td>
                <td className={pred.predicted_cve_severity > 8.0 ? "high-severity" : ""}>{pred.predicted_cve_severity.toFixed(1)} / 10.0</td>
                <td>{pred.vulnerability_type}</td>
                <td>{new Date(pred.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
