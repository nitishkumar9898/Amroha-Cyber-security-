import React, { useState, useEffect } from "react";
import axios from "axios";
import "./AdversaryDefenderDashboard.css";

export const AdversaryDefenderDashboard: React.FC = () => {
  const [detections, setDetections] = useState<any[]>([]);
  const [dataset, setDataset] = useState("");
  const [sampleId, setSampleId] = useState("");
  const [isDetecting, setIsDetecting] = useState(false);

  useEffect(() => {
    fetchDetections();
  }, []);

  const fetchDetections = () => {
    axios.get("/api/adversarydefender/detections").then(res => setDetections(res.data)).catch(console.error);
  };

  const handleDetect = () => {
    setIsDetecting(true);
    axios.post("/api/adversarydefender/detect", { dataset_name: dataset, sample_id: sampleId })
      .then(() => {
        fetchDetections();
        setDataset(""); setSampleId("");
      })
      .catch(console.error)
      .finally(() => setIsDetecting(false));
  };

  return (
    <div className="ad-container">
      <h2>AdversaryDefender Dashboard</h2>
      
      <div className="ad-card">
        <h3>Detect Data Poisoning</h3>
        <input placeholder="Dataset Name (e.g., TrainingData_v2)" value={dataset} onChange={e => setDataset(e.target.value)} />
        <input placeholder="Sample ID" value={sampleId} onChange={e => setSampleId(e.target.value)} />
        <button onClick={handleDetect} disabled={isDetecting}>{isDetecting ? "Scanning..." : "Scan Sample"}</button>
      </div>

      <div className="ad-card">
        <h3>Detection Log</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Dataset</th>
              <th>Sample ID</th>
              <th>Poison Probability</th>
              <th>Perturbation Type</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {detections.map(det => (
              <tr key={det.id}>
                <td>{det.id}</td>
                <td>{det.dataset_name}</td>
                <td>{det.sample_id}</td>
                <td className={det.poison_probability > 0.8 ? "high-poison" : ""}>{(det.poison_probability * 100).toFixed(1)}%</td>
                <td>{det.perturbation_type}</td>
                <td>{new Date(det.detected_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
