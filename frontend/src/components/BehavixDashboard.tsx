import React, { useState, useEffect } from "react";
import axios from "axios";
import "./BehavixDashboard.css";

export const BehavixDashboard: React.FC = () => {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [username, setUsername] = useState("");
  const [sessionMetrics, setSessionMetrics] = useState({ username: "", keystroke_speed: 1.0, mouse_jerkiness: 1.0, interaction_frequency: 1.0 });
  const [anomaly, setAnomaly] = useState<any>(null);

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = () => {
    axios.get("/api/behavix/profiles").then(res => setProfiles(res.data)).catch(console.error);
  };

  const handleCreateProfile = () => {
    axios.post("/api/behavix/profiles", { username })
      .then(() => {
        fetchProfiles();
        setUsername("");
      })
      .catch(console.error);
  };

  const handleAnalyzeSession = () => {
    axios.post("/api/behavix/analyze-session", sessionMetrics)
      .then(res => {
        setAnomaly(res.data);
        fetchProfiles();
      })
      .catch(console.error);
  };

  return (
    <div className="bx-container">
      <h2>Behavix Dashboard</h2>
      
      <div className="bx-card">
        <h3>Register New Baseline Profile</h3>
        <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
        <button onClick={handleCreateProfile}>Create Profile</button>
      </div>

      <div className="bx-card">
        <h3>Simulate Live Session Analysis</h3>
        <input placeholder="Username" value={sessionMetrics.username} onChange={e => setSessionMetrics({...sessionMetrics, username: e.target.value})} />
        <input type="number" step="0.1" placeholder="Keystroke Speed" value={sessionMetrics.keystroke_speed} onChange={e => setSessionMetrics({...sessionMetrics, keystroke_speed: parseFloat(e.target.value)})} />
        <input type="number" step="0.1" placeholder="Mouse Jerkiness" value={sessionMetrics.mouse_jerkiness} onChange={e => setSessionMetrics({...sessionMetrics, mouse_jerkiness: parseFloat(e.target.value)})} />
        <button onClick={handleAnalyzeSession}>Analyze Dynamics</button>
      </div>

      {anomaly && (
        <div className={`bx-card ${anomaly.anomaly_detected ? "bx-alert" : "bx-success"}`}>
          <h3>Analysis Result for {anomaly.username}</h3>
          <p><strong>Status:</strong> {anomaly.anomaly_detected ? "Anomaly Detected!" : "Normal"}</p>
          <p><strong>Risk Score:</strong> {(anomaly.risk_score * 100).toFixed(1)}%</p>
          <p><strong>Reason:</strong> {anomaly.reason}</p>
          <button onClick={() => setAnomaly(null)}>Dismiss</button>
        </div>
      )}

      <div className="bx-card">
        <h3>User Behavioral Profiles</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Base Keystrokes</th>
              <th>Base Mouse</th>
              <th>Current Risk Score</th>
              <th>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {profiles.map(p => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>{p.username}</td>
                <td>{p.baseline_keystroke_dynamics.toFixed(2)}</td>
                <td>{p.baseline_mouse_patterns.toFixed(2)}</td>
                <td style={{color: p.current_risk_score > 0.5 ? "red" : "inherit"}}>{(p.current_risk_score * 100).toFixed(1)}%</td>
                <td>{new Date(p.last_updated).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
