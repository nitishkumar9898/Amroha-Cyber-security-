import React, { useEffect, useState } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import useCollaboration from '../hooks/useCollaboration';
import PerformanceHUD from './PerformanceHUD';
import './training.css';

const TrainingArena: React.FC = () => {
  const { sessionId, sendAction } = useCollaboration();
  const { gl } = useThree();

  const [scenario, setScenario] = useState<any>(null);
  const [runId, setRunId] = useState<number | null>(null);
  const [simulationState, setSimulationState] = useState<string>("IDLE");
  const [analysis, setAnalysis] = useState<any>(null);
  const [actionLog, setActionLog] = useState<string[]>([]);

  // Enable WebXR on the canvas
  useEffect(() => {
    if (gl.xr) {
      gl.xr.enabled = true;
    }
  }, [gl]);

  const generateScenario = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/redteam/scenarios/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: "Auto-Generated Exercise", description: "Blue vs Red" })
      });
      const data = await res.json();
      setScenario(data);
      setActionLog(prev => [...prev, "Generated scenario: " + data.name]);
    } catch (e) {
      console.error(e);
    }
  };

  const startSimulation = async () => {
    if (!scenario) return;
    try {
      const res = await fetch('http://localhost:8000/api/redteam/simulation/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenario.id })
      });
      const data = await res.json();
      setRunId(data.id);
      setSimulationState(data.status);
      setActionLog(prev => [...prev, "Started simulation run: " + data.id]);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNodeClick = async (nodeId: string) => {
    // Both send to websocket and submit redteam action
    sendAction('node_click', { nodeId, sessionId });
    
    if (runId && simulationState === "IN_PROGRESS") {
      try {
        const res = await fetch(`http://localhost:8000/api/redteam/simulation/${runId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ team: 'blue', action_type: 'defend', target: nodeId })
        });
        const data = await res.json();
        setActionLog(prev => [...prev, `Action applied: ${data.action_result?.message || 'Unknown result'}`]);
        
        if (data.simulation_state === 'blue_win' || data.simulation_state === 'red_win') {
            setSimulationState("COMPLETED");
            setActionLog(prev => [...prev, `Simulation ended: ${data.simulation_state}`]);
        }
      } catch (e) {
        console.error(e);
      }
    }
  };

  const getAnalysis = async () => {
    if (!runId) return;
    try {
      const res = await fetch(`http://localhost:8000/api/redteam/simulation/${runId}/analysis`);
      const data = await res.json();
      setAnalysis(data);
    } catch (e) {
      console.error(e);
    }
  };

  // Rendering nodes dynamically from scenario graph
  const nodes = scenario?.attack_graph?.nodes || [];

  return (
    <div className="training-arena" style={{ display: 'flex', flexDirection: 'row', height: '100vh', width: '100vw' }}>
      
      {/* 3D Canvas Area */}
      <div style={{ flex: 1, position: 'relative' }}>
        <PerformanceHUD />
        <Canvas camera={{ position: [0, 0, 10] }}>
          <ambientLight intensity={0.3} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          <OrbitControls enableZoom enablePan enableRotate />
          
          {/* Default node if no scenario */}
          {nodes.length === 0 && (
              <mesh position={[0, 0, 0]} onClick={() => handleNodeClick("1")}>
                <icosahedronGeometry args={[0.5, 1]} />
                <meshStandardMaterial color="#ff003c" />
                <Html distanceFactor={10} position={[0, -1, 0]}>
                  <div className="hud-label" style={{ color: 'white', background: 'rgba(0,0,0,0.5)', padding: '5px' }}>Training Node</div>
                </Html>
              </mesh>
          )}

          {/* Render scenario nodes linearly */}
          {nodes.map((node: any, idx: number) => {
              const x = (idx - nodes.length / 2) * 2.5;
              return (
                  <mesh key={node.id} position={[x, 0, 0]} onClick={() => handleNodeClick(node.id)}>
                    <icosahedronGeometry args={[0.6, 1]} />
                    <meshStandardMaterial color={node.type === "target" ? "#ff0000" : "#00ffcc"} />
                    <Html distanceFactor={10} position={[0, -1.2, 0]}>
                      <div className="hud-label" style={{ color: 'white', background: 'rgba(0,0,0,0.7)', padding: '5px', borderRadius: '4px', textAlign: 'center' }}>
                          <b>{node.id}</b><br/>
                          <small>{node.type}</small>
                      </div>
                    </Html>
                  </mesh>
              )
          })}
        </Canvas>
      </div>

      {/* Control Panel Area */}
      <div style={{ width: '350px', background: '#1e1e1e', color: '#fff', padding: '20px', overflowY: 'auto' }}>
          <h2>RedTeamForge Control</h2>
          
          <div style={{ marginBottom: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button onClick={generateScenario} style={{ padding: '10px', background: '#007ACC', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>1. Generate Scenario</button>
              <button onClick={startSimulation} disabled={!scenario || runId !== null} style={{ padding: '10px', background: (!scenario || runId !== null) ? '#555' : '#28A745', color: 'white', border: 'none', borderRadius: '4px', cursor: (!scenario || runId !== null) ? 'not-allowed' : 'pointer' }}>2. Start Simulation</button>
              <button onClick={getAnalysis} disabled={simulationState !== "COMPLETED"} style={{ padding: '10px', background: simulationState !== "COMPLETED" ? '#555' : '#FFC107', color: 'black', border: 'none', borderRadius: '4px', cursor: simulationState !== "COMPLETED" ? 'not-allowed' : 'pointer' }}>3. Get Analysis Report</button>
          </div>

          <div style={{ marginBottom: '20px' }}>
              <strong>Status:</strong> {simulationState}
          </div>

          {analysis && (
              <div style={{ marginBottom: '20px', background: '#333', padding: '10px', borderRadius: '4px' }}>
                  <h3>Analysis Report</h3>
                  <p><b>Vulnerabilities Found:</b> {analysis.total_vulnerabilities_found}</p>
                  <h4>Recommendations:</h4>
                  <ul style={{ paddingLeft: '20px' }}>
                      {analysis.recommendations.map((r: string, i: number) => <li key={i}>{r}</li>)}
                  </ul>
              </div>
          )}

          <div>
              <h3>Action Log</h3>
              <ul style={{ paddingLeft: '20px', fontSize: '0.9em', maxHeight: '300px', overflowY: 'auto' }}>
                  {actionLog.map((log, i) => <li key={i}>{log}</li>)}
              </ul>
          </div>
      </div>
    </div>
  );
};

export default TrainingArena;
