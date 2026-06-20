import React, { useState, useEffect } from "react";
import axios from "axios";
import "./LearnForgeDashboard.css";

export const LearnForgeDashboard: React.FC = () => {
  const [lessons, setLessons] = useState<any[]>([]);
  const [incidentId, setIncidentId] = useState("");
  const [reportText, setReportText] = useState("");
  const [graphUpdate, setGraphUpdate] = useState<any>(null);

  useEffect(() => {
    fetchLessons();
  }, []);

  const fetchLessons = () => {
    axios.get("/api/learnforge/lessons").then(res => setLessons(res.data)).catch(console.error);
  };

  const handleExtract = () => {
    axios.post("/api/learnforge/extract", { incident_id: incidentId, raw_report_text: reportText })
      .then(() => {
        fetchLessons();
        setIncidentId(""); setReportText("");
      })
      .catch(console.error);
  };

  const handleUpdateGraph = (id: number) => {
    axios.post(`/api/learnforge/lessons/${id}/update-graph`)
      .then(res => {
        setGraphUpdate(res.data);
        fetchLessons();
      })
      .catch(console.error);
  };

  return (
    <div className="lf-container">
      <h2>LearnForge Dashboard</h2>
      
      <div className="lf-card">
        <h3>Extract Post-Incident Lessons</h3>
        <input placeholder="Incident ID" value={incidentId} onChange={e => setIncidentId(e.target.value)} />
        <textarea placeholder="Paste Raw Incident Report Here..." value={reportText} onChange={e => setReportText(e.target.value)} />
        <button onClick={handleExtract}>Extract Knowledge</button>
      </div>

      {graphUpdate && (
        <div className="lf-card lf-success">
          <h3>Knowledge Graph Updated</h3>
          <p>Lesson ID: {graphUpdate.lesson_id}</p>
          <p>Nodes Added: {graphUpdate.nodes_added}</p>
          <p>Edges Added: {graphUpdate.edges_added}</p>
          <button onClick={() => setGraphUpdate(null)}>Dismiss</button>
        </div>
      )}

      <div className="lf-card">
        <h3>Extracted Lessons Repository</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Incident ID</th>
              <th>Knowledge snippet</th>
              <th>Relevance</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {lessons.map(lesson => (
              <tr key={lesson.id}>
                <td>{lesson.id}</td>
                <td>{lesson.incident_id}</td>
                <td>{lesson.extracted_knowledge}</td>
                <td>{(lesson.relevance_score * 100).toFixed(1)}%</td>
                <td>{lesson.status}</td>
                <td>
                  <button className="graph-btn" onClick={() => handleUpdateGraph(lesson.id)} disabled={lesson.status === "Graph Updated"}>
                    {lesson.status === "Graph Updated" ? "Synced" : "Sync to Graph"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
