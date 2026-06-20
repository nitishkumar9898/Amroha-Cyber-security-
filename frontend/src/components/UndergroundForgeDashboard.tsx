import React, { useState, useEffect } from "react";
import axios from "axios";
import "./UndergroundForgeDashboard.css";

export const UndergroundForgeDashboard: React.FC = () => {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [url, setUrl] = useState("");
  const [keyword, setKeyword] = useState("");
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = () => {
    axios.get("/api/undergroundforge/alerts").then(res => setAlerts(res.data)).catch(console.error);
  };

  const handleScan = () => {
    setIsScanning(true);
    axios.post("/api/undergroundforge/scan", { marketplace_url: url, target_keyword: keyword })
      .then(() => {
        fetchAlerts();
        setUrl(""); setKeyword("");
      })
      .catch(console.error)
      .finally(() => setIsScanning(false));
  };

  return (
    <div className="ug-container">
      <h2>UndergroundForge Dashboard</h2>
      
      <div className="ug-card">
        <h3>Dark Web Marketplace Scanner</h3>
        <input placeholder="Marketplace Onion URL" value={url} onChange={e => setUrl(e.target.value)} />
        <input placeholder="Target Keyword (e.g., AmrohaCorp, 0-day)" value={keyword} onChange={e => setKeyword(e.target.value)} />
        <button onClick={handleScan} disabled={isScanning}>{isScanning ? "Scanning..." : "Launch Scan"}</button>
      </div>

      <div className="ug-card">
        <h3>Underground Intelligence Alerts</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Marketplace</th>
              <th>Keyword</th>
              <th>Match Context</th>
              <th>Threat Level</th>
              <th>Scraped At</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map(alert => (
              <tr key={alert.id}>
                <td>{alert.id}</td>
                <td>{alert.marketplace}</td>
                <td>{alert.keyword}</td>
                <td>{alert.match_context}</td>
                <td className={alert.threat_level > 0.8 ? "high-threat" : ""}>{(alert.threat_level * 10).toFixed(1)} / 10</td>
                <td>{new Date(alert.scraped_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
