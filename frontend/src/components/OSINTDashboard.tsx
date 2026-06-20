import React, { useState, useEffect } from "react";
import { startCrawl, getJobStatus, fetchNetwork, fetchMisinformation, fetchSummary } from "../api/osint";
import type { MisinformationEvent } from "../api/osint";
import "./OSINTDashboard.css";

interface NetworkNode {
  id: string;
  label: string;
  val: number;
  risk_score: number;
  affiliations: string[];
  platform: string;
}

interface NetworkEdge {
  source: string;
  target: string;
  weight: number;
  type: string;
}

export const OSINTDashboard: React.FC = () => {
  const [platform, setPlatform] = useState<string>("twitter");
  const [query, setQuery] = useState<string>("");
  const [activeJobId, setActiveJobId] = useState<number | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("");
  const [logs, setLogs] = useState<string[]>([]);
  const [summary, setSummary] = useState<string>("");
  const [nodes, setNodes] = useState<NetworkNode[]>([]);
  const [edges, setEdges] = useState<NetworkEdge[]>([]);
  const [misinfo, setMisinfo] = useState<MisinformationEvent[]>([]);
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [isCrawling, setIsCrawling] = useState<boolean>(false);

  // Poll for job completions
  useEffect(() => {
    if (activeJobId === null) return;
    
    const interval = setInterval(async () => {
      try {
        const job = await getJobStatus(activeJobId);
        setJobStatus(job.status);
        
        if (job.status === "completed") {
          clearInterval(interval);
          setIsCrawling(false);
          addLog("Crawl job finished. Processing actor network & NLP summary...");
          loadData();
        } else if (job.status === "failed") {
          clearInterval(interval);
          setIsCrawling(false);
          addLog("CRITICAL: Crawler returned error status. Check API key configs.");
        } else {
          addLog(`Crawling active: status is ${job.status}...`);
        }
      } catch (err) {
        console.error(err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [activeJobId]);

  // Load Initial Data
  const loadData = async () => {
    try {
      const net = await fetchNetwork();
      setNodes(net.nodes || []);
      setEdges(net.edges || []);
      
      const mis = await fetchMisinformation();
      setMisinfo(mis || []);
      
      if (query) {
        const sum = await fetchSummary(query);
        setSummary(sum.summary || "");
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const addLog = (msg: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [`[${time}] ${msg}`, ...prev.slice(0, 15)]);
  };

  const handleStartCrawl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setIsCrawling(true);
    setJobStatus("pending");
    setSummary("");
    addLog(`Initiating crawling job on platform [${platform.toUpperCase()}] for query: "${query}"`);

    try {
      const job = await startCrawl(platform, query);
      setActiveJobId(job.id);
      setJobStatus(job.status);
      addLog(`Job queued successfully. Assigned Job ID: #${job.id}`);
    } catch (err) {
      setIsCrawling(false);
      addLog(`Error triggering job: ${err}`);
    }
  };

  // Node position mapping (mock layout for visual SVG rendering)
  const getCoordinates = (index: number, total: number) => {
    if (total <= 1) return { x: 250, y: 150 };
    const radius = 95;
    const angle = (index / total) * 2 * Math.PI;
    return {
      x: 250 + radius * Math.cos(angle),
      y: 150 + radius * Math.sin(angle),
    };
  };

  return (
    <div className="osint-container">
      {/* Header Panel */}
      <div className="osint-header glass-card">
        <div className="header-meta">
          <span className="badge-live animate-pulse">OSINT CORE</span>
          <h1>OSINTForge</h1>
          <p className="subtitle">
            Ethical Open-Source Intelligence, Multi-Platform Crawler & Misinformation Spread Tracking
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="osint-grid">
        
        {/* Left Control & Crawl Panel */}
        <div className="osint-left-col">
          <div className="glass-card control-panel">
            <h2>Crawl Scheduler</h2>
            <form onSubmit={handleStartCrawl} className="crawl-form">
              <div className="form-group">
                <label>Platform Source</label>
                <div className="platform-selector">
                  <button
                    type="button"
                    className={platform === "twitter" ? "active" : ""}
                    onClick={() => setPlatform("twitter")}
                  >
                    Twitter/X
                  </button>
                  <button
                    type="button"
                    className={platform === "reddit" ? "active" : ""}
                    onClick={() => setPlatform("reddit")}
                  >
                    Reddit
                  </button>
                  <button
                    type="button"
                    className={platform === "mastodon" ? "active" : ""}
                    onClick={() => setPlatform("mastodon")}
                  >
                    Mastodon
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label>Target Query / HashTag</label>
                <input
                  type="text"
                  placeholder="e.g. #zero_day, ransomware"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="osint-input"
                  required
                />
              </div>

              <button
                type="submit"
                className={`submit-btn ${isCrawling ? "loading" : ""}`}
                disabled={isCrawling}
              >
                {isCrawling ? "Crawling Data..." : "Execute Search Job"}
              </button>
            </form>

            {jobStatus && (
              <div className="status-indicator">
                <span>Job Status: </span>
                <span className={`status-badge ${jobStatus.toLowerCase()}`}>{jobStatus.toUpperCase()}</span>
              </div>
            )}
          </div>

          {/* Crawler Log Output */}
          <div className="glass-card log-panel">
            <h2>Active Console Logs</h2>
            <div className="console-box">
              {logs.length === 0 ? (
                <div className="empty-state">Console idle. Awaiting crawler job execution.</div>
              ) : (
                logs.map((log, idx) => <div key={idx} className="log-line">{log}</div>)
              )}
            </div>
          </div>
        </div>

        {/* Right Dashboard Visualization Area */}
        <div className="osint-right-col">
          
          {/* AI Summarization Panel */}
          {summary && (
            <div className="glass-card ai-summary-panel">
              <div className="card-header">
                <span className="icon">🤖</span>
                <h2>Generative AI Analysis & Insights</h2>
              </div>
              <p className="summary-text">{summary}</p>
            </div>
          )}

          {/* Interactive Actor Network Visualization */}
          <div className="glass-card network-panel">
            <div className="card-header">
              <span className="icon">🕸️</span>
              <h2>Threat Actor Profiling & Network</h2>
            </div>
            
            <div className="network-vis-container">
              {nodes.length === 0 ? (
                <div className="empty-state">No actor graph available. Run a query crawl to construct relationships.</div>
              ) : (
                <div className="network-split">
                  <div className="svg-container">
                    <svg viewBox="0 0 500 300" className="network-svg">
                      <defs>
                        <radialGradient id="highRiskGrad" cx="50%" cy="50%" r="50%">
                          <stop offset="0%" stopColor="#ff2e93" />
                          <stop offset="100%" stopColor="#a3004a" />
                        </radialGradient>
                        <radialGradient id="lowRiskGrad" cx="50%" cy="50%" r="50%">
                          <stop offset="0%" stopColor="#00e5ff" />
                          <stop offset="100%" stopColor="#005b66" />
                        </radialGradient>
                      </defs>
                      
                      {/* Edges */}
                      {edges.map((e, idx) => {
                        const sIdx = nodes.findIndex(n => n.id === e.source);
                        const tIdx = nodes.findIndex(n => n.id === e.target);
                        if (sIdx === -1 || tIdx === -1) return null;
                        const sCoords = getCoordinates(sIdx, nodes.length);
                        const tCoords = getCoordinates(tIdx, nodes.length);
                        
                        return (
                          <line
                            key={idx}
                            x1={sCoords.x}
                            y1={sCoords.y}
                            x2={tCoords.x}
                            y2={tCoords.y}
                            className={`network-edge ${hoveredNode === e.source || hoveredNode === e.target ? "highlighted" : ""}`}
                            strokeWidth={e.weight}
                          />
                        );
                      })}

                      {/* Nodes */}
                      {nodes.map((n, idx) => {
                        const coords = getCoordinates(idx, nodes.length);
                        const isHighRisk = n.risk_score >= 0.7;
                        
                        return (
                          <g
                            key={n.id}
                            transform={`translate(${coords.x}, ${coords.y})`}
                            onClick={() => setSelectedNode(n)}
                            onMouseEnter={() => setHoveredNode(n.id)}
                            onMouseLeave={() => setHoveredNode(null)}
                            style={{ cursor: "pointer" }}
                          >
                            <circle
                              r={n.risk_score * 12 + 8}
                              fill={isHighRisk ? "url(#highRiskGrad)" : "url(#lowRiskGrad)"}
                              className={`network-node ${selectedNode?.id === n.id ? "selected" : ""}`}
                            />
                            <text
                              y={n.risk_score * 12 + 20}
                              textAnchor="middle"
                              className="node-label"
                            >
                              {n.label}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  </div>

                  {/* Profiling Details */}
                  <div className="actor-profile-sidebar">
                    {selectedNode ? (
                      <div className="actor-details">
                        <div className="risk-score-gauge">
                          <span className="gauge-label">Risk Rating</span>
                          <span className={`gauge-value ${selectedNode.risk_score >= 0.7 ? "high" : "low"}`}>
                            {Math.round(selectedNode.risk_score * 100)}%
                          </span>
                        </div>
                        <h3>Hashed ID:</h3>
                        <p className="hashed-name">{selectedNode.id.replace("node_", "")}</p>
                        
                        <h3>Platform Presence:</h3>
                        <div className="platforms">
                          <span className="platform-tag">{selectedNode.platform}</span>
                        </div>

                        <h3>Affiliations & Signals:</h3>
                        <ul>
                          {selectedNode.affiliations.map((aff, i) => (
                            <li key={i}>{aff}</li>
                          ))}
                        </ul>

                        {selectedNode.risk_score >= 0.7 && (
                          <div className="darkweb-alert animate-pulse">
                            ⚠️ DarkWeb Attribution Detected
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="details-placeholder">
                        Click on a network node to inspect threat actor profile attributes.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Misinformation Spread Tracking Section */}
          <div className="glass-card misinformation-panel">
            <div className="card-header">
              <span className="icon">⚠️</span>
              <h2>Misinformation Tracking & Credibility Alerts</h2>
            </div>
            
            <div className="misinfo-table-container">
              {misinfo.length === 0 ? (
                <div className="empty-state">No credibility warnings matching current crawls.</div>
              ) : (
                <table className="misinfo-table">
                  <thead>
                    <tr>
                      <th>Identified Claim</th>
                      <th>Fact Check Link</th>
                      <th>Misinfo Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {misinfo.map((m) => (
                      <tr key={m.id}>
                        <td className="claim-cell">{m.claim_text}</td>
                        <td>
                          {m.fact_check_url ? (
                            <a href={m.fact_check_url} target="_blank" rel="noreferrer" className="fact-link">
                              PIB FactCheck ↗
                            </a>
                          ) : (
                            <span className="warning-text">Pending Verification</span>
                          )}
                        </td>
                        <td>
                          <div className="confidence-pill" style={{ opacity: m.confidence }}>
                            {Math.round(m.confidence * 100)}%
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
