import React, { useState, useEffect } from "react";
import axios from "axios";
import "./FirmwareGuardDashboard.css";

export const FirmwareGuardDashboard: React.FC = () => {
  const [firmwares, setFirmwares] = useState<any[]>([]);
  const [deviceModel, setDeviceModel] = useState("");
  const [version, setVersion] = useState("");
  const [fileHash, setFileHash] = useState("");
  const [isSigned, setIsSigned] = useState(false);

  useEffect(() => {
    fetchFirmwares();
  }, []);

  const fetchFirmwares = () => {
    axios.get("/api/firmwareguard/firmware").then(res => setFirmwares(res.data)).catch(console.error);
  };

  const handleUpload = () => {
    axios.post("/api/firmwareguard/firmware", { device_model: deviceModel, version, file_hash: fileHash, is_signed: isSigned })
      .then(() => {
        fetchFirmwares();
        setDeviceModel(""); setVersion(""); setFileHash(""); setIsSigned(false);
      })
      .catch(console.error);
  };

  const handleAnalyze = (id: number) => {
    axios.post(`/api/firmwareguard/firmware/${id}/analyze`)
      .then(() => fetchFirmwares())
      .catch(console.error);
  };

  return (
    <div className="fg-container">
      <h2>FirmwareGuard Dashboard</h2>
      
      <div className="fg-card">
        <h3>Register Firmware Image</h3>
        <input placeholder="Device Model" value={deviceModel} onChange={e => setDeviceModel(e.target.value)} />
        <input placeholder="Version" value={version} onChange={e => setVersion(e.target.value)} />
        <input placeholder="File Hash (SHA256)" value={fileHash} onChange={e => setFileHash(e.target.value)} />
        <label>
          <input type="checkbox" checked={isSigned} onChange={e => setIsSigned(e.target.checked)} />
          Is Signed
        </label>
        <button onClick={handleUpload}>Register</button>
      </div>

      <div className="fg-card">
        <h3>Firmware Inventory</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Model</th>
              <th>Version</th>
              <th>Signed</th>
              <th>Risk Score</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {firmwares.map(fw => (
              <tr key={fw.id}>
                <td>{fw.id}</td>
                <td>{fw.device_model}</td>
                <td>{fw.version}</td>
                <td>{fw.is_signed ? "Yes" : "No"}</td>
                <td>{(fw.risk_score * 10).toFixed(1)}/10</td>
                <td>{fw.status}</td>
                <td>
                  <button className="analyze-btn" onClick={() => handleAnalyze(fw.id)}>Analyze</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
