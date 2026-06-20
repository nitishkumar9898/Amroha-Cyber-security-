import React, { useState, useEffect } from "react";
import axios from "axios";
import "./CorrelixDashboard.css";

export const CorrelixDashboard: React.FC = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("");
  const [graphData, setGraphData] = useState<any>(null);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = () => {
    axios.get("/api/correlix/jobs").then(res => setJobs(res.data)).catch(console.error);
  };

  const handleCorrelate = () => {
    axios.post("/api/correlix/correlate", { source_module: source, target_module: target })
      .then(() => {
        fetchJobs();
        setSource(""); setTarget("");
      })
      .catch(console.error);
  };

  const handleViewGraph = (id: number) => {
    axios.get(`/api/correlix/jobs/${id}/graph`)
      .then(res => setGraphData(res.data))
      .catch(console.error);
  };

  return (
    <div className="cx-container">
      <h2>Correlix Dashboard</h2>
      
      <div className="cx-card">
        <h3>New Correlation Job</h3>
        <input placeholder="Source Module (e.g., FirmwareGuard)" value={source} onChange={e => setSource(e.target.value)} />
        <input placeholder="Target Module (e.g., PsyOpsForge)" value={target} onChange={e => setTarget(e.target.value)} />
        <button onClick={handleCorrelate}>Run Correlation</button>
      </div>

      {graphData && (
        <div className="cx-card cx-graph">
          <h3>Correlation Graph (Job #{graphData.job_id})</h3>
          <div className="cx-nodes">
            <h4>Nodes:</h4>
            <ul>
              {graphData.nodes.map((n: any) => <li key={n.id}>[{n.type}] {n.label}</li>)}
            </ul>
          </div>
          <div className="cx-links">
            <h4>Links:</h4>
            <ul>
              {graphData.links.map((l: any, i: number) => <li key={i}>{l.source} --({l.relationship})--&gt; {l.target} [Weight: {l.weight}]</li>)}
            </ul>
          </div>
          <button onClick={() => setGraphData(null)}>Close Graph</button>
        </div>
      )}

      <div className="cx-card">
        <h3>Correlation Jobs</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>Target</th>
              <th>Confidence</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map(job => (
              <tr key={job.id}>
                <td>{job.id}</td>
                <td>{job.source_module}</td>
                <td>{job.target_module}</td>
                <td>{(job.confidence_score * 100).toFixed(1)}%</td>
                <td>{job.status}</td>
                <td>
                  <button className="graph-btn" onClick={() => handleViewGraph(job.id)}>View Graph</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
