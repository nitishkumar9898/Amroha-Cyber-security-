import React, { useState, useEffect } from "react";
import axios from "axios";
import "./CollabSpaceDashboard.css";

export const CollabSpaceDashboard: React.FC = () => {
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [wsName, setWsName] = useState("");
  const [wsOwner, setWsOwner] = useState("");
  const [activeWs, setActiveWs] = useState<number | null>(null);
  const [annotations, setAnnotations] = useState<any[]>([]);
  const [newAnnotation, setNewAnnotation] = useState("");
  const [author, setAuthor] = useState("");

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  useEffect(() => {
    if (activeWs !== null) {
      fetchAnnotations(activeWs);
    }
  }, [activeWs]);

  const fetchWorkspaces = () => {
    axios.get("/api/collabspace/workspaces").then(res => setWorkspaces(res.data)).catch(console.error);
  };

  const fetchAnnotations = (id: number) => {
    axios.get(`/api/collabspace/workspaces/${id}/annotations`).then(res => setAnnotations(res.data)).catch(console.error);
  };

  const handleCreateWs = () => {
    axios.post("/api/collabspace/workspaces", { name: wsName, owner: wsOwner })
      .then(() => {
        fetchWorkspaces();
        setWsName(""); setWsOwner("");
      })
      .catch(console.error);
  };

  const handleAddAnnotation = () => {
    if (activeWs === null) return;
    axios.post("/api/collabspace/annotations", { workspace_id: activeWs, author: author, content: newAnnotation })
      .then(() => {
        fetchAnnotations(activeWs);
        setNewAnnotation("");
      })
      .catch(console.error);
  };

  return (
    <div className="cs-container">
      <h2>CollabSpace Dashboard</h2>
      
      <div className="cs-card">
        <h3>Create Workspace</h3>
        <input placeholder="Workspace Name" value={wsName} onChange={e => setWsName(e.target.value)} />
        <input placeholder="Owner Name" value={wsOwner} onChange={e => setWsOwner(e.target.value)} />
        <button onClick={handleCreateWs}>Create</button>
      </div>

      <div className="cs-layout">
        <div className="cs-sidebar">
          <h3>Active Workspaces</h3>
          <ul>
            {workspaces.map(ws => (
              <li 
                key={ws.id} 
                className={activeWs === ws.id ? "active-ws" : ""} 
                onClick={() => setActiveWs(ws.id)}
              >
                {ws.name} ({ws.owner})
              </li>
            ))}
          </ul>
        </div>

        <div className="cs-main">
          {activeWs ? (
            <>
              <h3>Live Investigation feed</h3>
              <div className="cs-annotations">
                {annotations.map(ann => (
                  <div key={ann.id} className="cs-annotation">
                    <strong>{ann.author}</strong> <span className="cs-date">{new Date(ann.created_at).toLocaleString()}</span>
                    <p>{ann.content}</p>
                  </div>
                ))}
              </div>
              <div className="cs-input-area">
                <input placeholder="Your Name" value={author} onChange={e => setAuthor(e.target.value)} className="author-input" />
                <input placeholder="Add annotation/evidence..." value={newAnnotation} onChange={e => setNewAnnotation(e.target.value)} className="content-input" />
                <button onClick={handleAddAnnotation}>Post</button>
              </div>
            </>
          ) : (
            <p>Select a workspace to view the live investigation feed.</p>
          )}
        </div>
      </div>
    </div>
  );
};
