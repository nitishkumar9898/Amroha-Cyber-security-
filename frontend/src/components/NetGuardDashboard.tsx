import React, { useState } from 'react';
import './NetGuardDashboard.css';

interface Node {
  id: number;
  node_name: string;
  node_type: string;
  ip_address: string;
  is_active: boolean;
}

interface AnalysisResult {
  node_id: number;
  is_anomalous: boolean;
  threat_type: string | null;
  confidence: number;
}

interface SimulationReport {
  node_id: number;
  simulation_type: string;
  predicted_impact_hours: number;
  recommended_action: string;
}

export default function NetGuardDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [nodes, setNodes] = useState<Node[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [forecast, setForecast] = useState<SimulationReport | null>(null);

  // Registration Form State
  const [nodeName, setNodeName] = useState('');
  const [nodeType, setNodeType] = useState('STANDARD');
  const [ipAddress, setIpAddress] = useState('10.0.0.1');

  // Traffic Ingestion Form State
  const [protocol, setProtocol] = useState('TCP');
  const [bytes, setBytes] = useState<number>(500);
  const [signature, setSignature] = useState('NORMAL_TRAFFIC');

  const handleRegisterNode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/netguard/nodes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_name: nodeName, node_type: nodeType, ip_address: ipAddress })
      });
      if (!response.ok) throw new Error('Failed to register node');
      const newNode = await response.json();
      setNodes([...nodes, newNode]);
      setNodeName('');
      setIpAddress('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeTraffic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNode) return;
    setLoading(true);
    setAnalysisResult(null);
    try {
      const response = await fetch('http://localhost:8000/api/netguard/analyze-traffic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: selectedNode.id,
          protocol,
          bytes_transferred: bytes,
          payload_signature: signature
        })
      });
      if (!response.ok) throw new Error('Failed to analyze traffic');
      setAnalysisResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateAttack = async (simType: string) => {
    if (!selectedNode) return;
    setLoading(true);
    setForecast(null);
    try {
      const response = await fetch('http://localhost:8000/api/netguard/simulate-attack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: selectedNode.id,
          simulation_type: simType
        })
      });
      if (!response.ok) throw new Error('Failed to simulate attack');
      setForecast(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="netguard-dashboard">
      <header className="ng-header">
        <h1>🌐 NetGuard Architect</h1>
        <p>5G/6G, SCADA, and DL-driven Network Forensics</p>
      </header>

      {error && <div className="ng-alert">{error}</div>}

      <div className="ng-grid">
        {/* Left Column: Infrastructure Management */}
        <div>
          <div className="ng-panel" style={{ marginBottom: '2rem' }}>
            <h2>🏗️ Register Infrastructure Node</h2>
            <form onSubmit={handleRegisterNode}>
              <div className="ng-form-group">
                <label>Node Name</label>
                <input type="text" value={nodeName} onChange={(e) => setNodeName(e.target.value)} required placeholder="e.g., Substation-PLC-01" />
              </div>
              <div className="ng-form-group">
                <label>Node Type</label>
                <select value={nodeType} onChange={(e) => setNodeType(e.target.value)}>
                  <option value="STANDARD">Standard Enterprise (DL Analysis)</option>
                  <option value="TELECOM">Telecom / 5G Core</option>
                  <option value="SCADA">SCADA / ICS</option>
                </select>
              </div>
              <div className="ng-form-group">
                <label>IP Address</label>
                <input type="text" value={ipAddress} onChange={(e) => setIpAddress(e.target.value)} required />
              </div>
              <button type="submit" className="ng-btn" disabled={loading}>Provision Node</button>
            </form>
          </div>

          {nodes.length > 0 && (
            <div className="ng-panel">
              <h2>📍 Active Topology</h2>
              {nodes.map(node => (
                <div 
                  key={node.id} 
                  className={`ng-node-card ${node.node_type.toLowerCase()}`}
                  style={{ cursor: 'pointer', opacity: selectedNode?.id === node.id ? 1 : 0.6 }}
                  onClick={() => { setSelectedNode(node); setAnalysisResult(null); setForecast(null); }}
                >
                  <div>
                    <strong>{node.node_name}</strong>
                    <div style={{ fontSize: '0.8rem', color: '#aaa', marginTop: '0.25rem' }}>{node.ip_address}</div>
                  </div>
                  <span className={`ng-badge ${node.node_type.toLowerCase()}`}>{node.node_type}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Traffic Injection & Forecasting */}
        <div>
          {!selectedNode ? (
            <div className="ng-panel" style={{ textAlign: 'center', color: '#888' }}>
              <p>Select a node from the topology to interact with it.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              
              {/* Traffic Ingestion */}
              <div className="ng-panel">
                <h2>📡 Inject Traffic Log (Node #{selectedNode.id})</h2>
                <form onSubmit={handleAnalyzeTraffic}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className="ng-form-group">
                      <label>Protocol</label>
                      <input type="text" value={protocol} onChange={(e) => setProtocol(e.target.value)} placeholder="e.g., MODBUS, GTP-U" required />
                    </div>
                    <div className="ng-form-group">
                      <label>Bytes</label>
                      <input type="number" value={bytes} onChange={(e) => setBytes(parseInt(e.target.value))} required />
                    </div>
                  </div>
                  <div className="ng-form-group">
                    <label>Payload Signature / Content</label>
                    <input type="text" value={signature} onChange={(e) => setSignature(e.target.value)} required />
                  </div>
                  <button type="submit" className="ng-btn" disabled={loading}>Run Inference</button>
                </form>

                {analysisResult && (
                  <div className="ng-analysis-result">
                    <div><span style={{ color: '#888' }}>Inference Complete:</span></div>
                    {analysisResult.is_anomalous ? (
                      <>
                        <div className="threat">DETECTED: {analysisResult.threat_type}</div>
                        <div><span style={{ color: '#888' }}>Confidence:</span> {(analysisResult.confidence * 100).toFixed(1)}%</div>
                      </>
                    ) : (
                      <div className="safe">TRAFFIC BENIGN (No Threats Detected)</div>
                    )}
                  </div>
                )}
              </div>

              {/* Threat Forecasting */}
              <div className="ng-panel">
                <h2>🔮 Predictive Forecasting</h2>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                  <button onClick={() => handleSimulateAttack('DDOS')} className="ng-btn" style={{ margin: 0, background: '#333', color: '#fff' }} disabled={loading}>Simulate DDoS</button>
                  <button onClick={() => handleSimulateAttack('APT')} className="ng-btn" style={{ margin: 0, background: '#333', color: '#fff' }} disabled={loading}>Simulate APT Campaign</button>
                </div>

                {forecast && (
                  <div className="ng-forecast-card">
                    <div style={{ color: '#888', textTransform: 'uppercase', marginBottom: '1rem', fontWeight: 'bold' }}>
                      {forecast.simulation_type} Impact Forecast
                    </div>
                    <div className="ng-forecast-time">{forecast.predicted_impact_hours} <span style={{ fontSize: '1rem' }}>HRS</span></div>
                    <div style={{ color: '#888', marginBottom: '1rem' }}>Estimated Time to Critical Service Impact</div>
                    <div style={{ background: '#222', padding: '1rem', borderRadius: '4px', textAlign: 'left' }}>
                      <strong style={{ color: '#ffaa00' }}>RECOMMENDED ACTION:</strong><br/>
                      {forecast.recommended_action}
                    </div>
                  </div>
                )}
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}
