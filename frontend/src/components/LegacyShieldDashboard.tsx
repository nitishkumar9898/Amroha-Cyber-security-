import React, { useState, useEffect } from "react";
import axios from "axios";
import "./LegacyShieldDashboard.css";

export const LegacyShieldDashboard: React.FC = () => {
  const [investigations, setInvestigations] = useState<any[]>([]);
  const [systemType, setSystemType] = useState("");
  const [protocol, setProtocol] = useState("");
  const [airGap, setAirGap] = useState("Intact");

  useEffect(() => {
    fetchInvestigations();
  }, []);

  const fetchInvestigations = () => {
    axios.get("/api/legacyshield/investigations").then(res => setInvestigations(res.data)).catch(console.error);
  };

  const handleInvestigate = () => {
    axios.post("/api/legacyshield/investigate", { system_type: systemType, protocol, air_gap_status: airGap })
      .then(() => {
        fetchInvestigations();
        setSystemType(""); setProtocol(""); setAirGap("Intact");
      })
      .catch(console.error);
  };

  return (
    <div className="ls-container">
      <h2>LegacyShield Dashboard</h2>
      
      <div className="ls-card">
        <h3>OT/Legacy System Assessment</h3>
        <input placeholder="System Type (e.g., Siemens SCADA)" value={systemType} onChange={e => setSystemType(e.target.value)} />
        <input placeholder="Protocol (e.g., Modbus/TCP)" value={protocol} onChange={e => setProtocol(e.target.value)} />
        <select value={airGap} onChange={e => setAirGap(e.target.value)} className="ls-select">
          <option value="Intact">Air-Gap Intact</option>
          <option value="Bridged">Air-Gap Bridged</option>
          <option value="Compromised">Air-Gap Compromised</option>
        </select>
        <button onClick={handleInvestigate}>Analyze Risk</button>
      </div>

      <div className="ls-card">
        <h3>Investigation Log</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>System Type</th>
              <th>Protocol</th>
              <th>Air-Gap Status</th>
              <th>Migration Risk</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {investigations.map(inv => (
              <tr key={inv.id}>
                <td>{inv.id}</td>
                <td>{inv.system_type}</td>
                <td>{inv.protocol}</td>
                <td>{inv.air_gap_status}</td>
                <td className={inv.migration_risk_score > 0.7 ? "high-risk" : ""}>{(inv.migration_risk_score * 100).toFixed(1)}%</td>
                <td>{new Date(inv.investigated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
