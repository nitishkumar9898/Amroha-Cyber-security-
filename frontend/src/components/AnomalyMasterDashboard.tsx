import React, { useState, useEffect } from "react";
import axios from "axios";
import "./AnomalyMasterDashboard.css";

export const AnomalyMasterDashboard: React.FC = () => {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [source, setSource] = useState("");
  const [observed, setObserved] = useState<number | string>("");
  const [expected, setExpected] = useState<number | string>("");

  useEffect(() => {
    fetchAnomalies();
  }, []);

  const fetchAnomalies = () => {
    axios.get("/api/anomalymaster/anomalies").then(res => setAnomalies(res.data)).catch(console.error);
  };

  const handleReport = () => {
    axios.post("/api/anomalymaster/report", { 
        metric_source: source, 
        observed_value: Number(observed), 
        expected_value: Number(expected) 
      })
      .then(() => {
        fetchAnomalies();
        setSource(""); setObserved(""); setExpected("");
      })
      .catch(console.error);
  };

  return (
    <div className="am-container">
      <h2>AnomalyMaster Dashboard</h2>
      
      <div className="am-card">
        <h3>Report System Metric</h3>
        <input placeholder="Metric Source (e.g., NetworkOut)" value={source} onChange={e => setSource(e.target.value)} />
        <input type="number" placeholder="Observed Value" value={observed} onChange={e => setObserved(e.target.value)} />
        <input type="number" placeholder="Expected Value" value={expected} onChange={e => setExpected(e.target.value)} />
        <button onClick={handleReport}>Analyze Anomaly</button>
      </div>

      <div className="am-card">
        <h3>Detected Anomalies & Root Causes</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>Observed</th>
              <th>Expected</th>
              <th>Deviation</th>
              <th>Root Cause Hypothesis</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {anomalies.map(anomaly => (
              <tr key={anomaly.id}>
                <td>{anomaly.id}</td>
                <td>{anomaly.metric_source}</td>
                <td>{anomaly.observed_value}</td>
                <td>{anomaly.expected_value}</td>
                <td className={anomaly.deviation_score > 0.5 ? "high-deviation" : ""}>{(anomaly.deviation_score * 100).toFixed(1)}%</td>
                <td>{anomaly.root_cause_hypothesis}</td>
                <td>{new Date(anomaly.detected_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
