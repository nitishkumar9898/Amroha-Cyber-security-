import React, { useState, useEffect } from "react";
import axios from "axios";
import "./SovereignGuardDashboard.css";

export const SovereignGuardDashboard: React.FC = () => {
  const [checks, setChecks] = useState<any[]>([]);
  const [classification, setClassification] = useState("");
  const [region, setRegion] = useState("");
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    fetchChecks();
  }, []);

  const fetchChecks = () => {
    axios.get("/api/sovereignguard/checks").then(res => setChecks(res.data)).catch(console.error);
  };

  const handleCheck = () => {
    setIsChecking(true);
    axios.post("/api/sovereignguard/check", { data_classification: classification, destination_region: region })
      .then(() => {
        fetchChecks();
        setClassification(""); setRegion("");
      })
      .catch(console.error)
      .finally(() => setIsChecking(false));
  };

  return (
    <div className="sg-container">
      <h2>SovereignGuard Dashboard</h2>
      
      <div className="sg-card">
        <h3>Verify Data Sovereignty Transfer</h3>
        <input placeholder="Data Classification (e.g., Top Secret)" value={classification} onChange={e => setClassification(e.target.value)} />
        <input placeholder="Destination Region (e.g., CN-EAST)" value={region} onChange={e => setRegion(e.target.value)} />
        <button onClick={handleCheck} disabled={isChecking}>{isChecking ? "Checking..." : "Verify Sovereignty"}</button>
      </div>

      <div className="sg-card">
        <h3>Sovereignty Check Log</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Classification</th>
              <th>Destination Region</th>
              <th>Compliance Status</th>
              <th>Violation Risk</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {checks.map(check => (
              <tr key={check.id}>
                <td>{check.id}</td>
                <td>{check.data_classification}</td>
                <td>{check.destination_region}</td>
                <td className={check.compliance_status === "Violated" ? "status-violated" : "status-compliant"}>{check.compliance_status}</td>
                <td>{(check.violation_risk_score * 100).toFixed(1)}%</td>
                <td>{new Date(check.checked_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
