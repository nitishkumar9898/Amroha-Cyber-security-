import React, { useState, useEffect } from "react";
import axios from "axios";
import "./VoiceGuardDashboard.css";

export const VoiceGuardDashboard: React.FC = () => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [fileHash, setFileHash] = useState("");
  const [speakerId, setSpeakerId] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = () => {
    axios.get("/api/voiceguard/tasks").then(res => setTasks(res.data)).catch(console.error);
  };

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    axios.post("/api/voiceguard/analyze", { audio_file_hash: fileHash, speaker_id: speakerId })
      .then(() => {
        fetchTasks();
        setFileHash(""); setSpeakerId("");
      })
      .catch(console.error)
      .finally(() => setIsAnalyzing(false));
  };

  return (
    <div className="vg-container">
      <h2>VoiceGuard Dashboard</h2>
      
      <div className="vg-card">
        <h3>Audio Forensics Analysis</h3>
        <input placeholder="Audio File Hash (SHA256)" value={fileHash} onChange={e => setFileHash(e.target.value)} />
        <input placeholder="Target Speaker ID (e.g., CEO_Fake)" value={speakerId} onChange={e => setSpeakerId(e.target.value)} />
        <button onClick={handleAnalyze} disabled={isAnalyzing}>{isAnalyzing ? "Analyzing..." : "Run Spectral Analysis"}</button>
      </div>

      <div className="vg-card">
        <h3>Forensics Log</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>File Hash</th>
              <th>Speaker ID</th>
              <th>Synthetic Probability</th>
              <th>Spectral Anomalies</th>
              <th>Analysis Time</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(task => (
              <tr key={task.id}>
                <td>{task.id}</td>
                <td>{task.audio_file_hash}</td>
                <td>{task.speaker_id}</td>
                <td className={task.synthetic_probability > 0.8 ? "high-prob" : ""}>{(task.synthetic_probability * 100).toFixed(1)}%</td>
                <td>{task.spectral_anomalies}</td>
                <td>{new Date(task.analyzed_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
