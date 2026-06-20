import React, { useState } from 'react';
import './SwarmForgeDashboard.css';

interface SwarmSimResult {
  simulation_id: number;
  status: string;
  initial_coordination_score: number;
}

interface AgentBehaviorReport {
  simulation_id: number;
  coordination_score: number;
  mutation_velocity: number;
  predicted_pivot_target: string;
}

interface CounterSwarmResult {
  simulation_id: number;
  strategy_used: string;
  neutralization_percentage: number;
  swarm_deactivated: boolean;
}

export default function SwarmForgeDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Attack State
  const [targetInfra, setTargetInfra] = useState('Edge-Gateway-Cluster');
  const [swarmSize, setSwarmSize] = useState<number>(5000);
  const [attackVector, setAttackVector] = useState('LATERAL_MOVEMENT');
  
  const [activeSimId, setActiveSimId] = useState<number | null>(null);
  const [simResult, setSimResult] = useState<SwarmSimResult | null>(null);

  // Telemetry State
  const [telemetry, setTelemetry] = useState<AgentBehaviorReport | null>(null);

  // Defense State
  const [strategy, setStrategy] = useState('HONEYPOT_DECOY');
  const [defenseResult, setDefenseResult] = useState<CounterSwarmResult | null>(null);

  const handleLaunchSwarm = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSimResult(null);
    setTelemetry(null);
    setDefenseResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/swarmforge/simulate-attack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_infrastructure: targetInfra,
          swarm_size: swarmSize,
          attack_vector: attackVector
        })
      });
      if (!response.ok) throw new Error('Failed to launch swarm');
      const data = await response.json();
      setSimResult(data);
      setActiveSimId(data.simulation_id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePollTelemetry = async () => {
    if (!activeSimId) return;
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/swarmforge/analyze-behavior/${activeSimId}`);
      if (!response.ok) throw new Error('Failed to fetch telemetry');
      setTelemetry(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeployDefense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSimId) return;
    setLoading(true);
    setDefenseResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/swarmforge/deploy-counter-swarm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_id: activeSimId,
          strategy_used: strategy
        })
      });
      if (!response.ok) throw new Error('Counter-swarm deployment failed');
      setDefenseResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="swarmforge-dashboard">
      <header className="sf-header">
        <h1>🐝 SwarmForge Architect</h1>
        <p>Multi-Agent Autonomous Swarms & Reinforcement Learning Defense</p>
      </header>

      {error && <div className="sf-alert">{error}</div>}

      <div className="sf-grid">
        {/* Left Column - Attack */}
        <div>
          <div className="sf-panel" style={{ marginBottom: '2rem' }}>
            <h2>🔴 Initialize Swarm Attack</h2>
            <form onSubmit={handleLaunchSwarm}>
              <div className="sf-form-group">
                <label>Target Infrastructure</label>
                <input type="text" value={targetInfra} onChange={(e) => setTargetInfra(e.target.value)} required />
              </div>
              <div className="sf-form-group">
                <label>Swarm Agent Count</label>
                <input type="number" value={swarmSize} onChange={(e) => setSwarmSize(parseInt(e.target.value))} required />
              </div>
              <div className="sf-form-group">
                <label>Attack Vector</label>
                <select value={attackVector} onChange={(e) => setAttackVector(e.target.value)}>
                  <option value="LATERAL_MOVEMENT">Lateral Movement</option>
                  <option value="DDOS">Coordinated DDoS</option>
                  <option value="DATA_EXFIL">Distributed Data Exfiltration</option>
                </select>
              </div>
              <button type="submit" className="sf-btn" disabled={loading}>Launch Autonomous Swarm</button>
            </form>

            {simResult && (
              <div style={{ marginTop: '1rem', color: '#ff3366' }}>
                ✓ Swarm Deployed [ID: {simResult.simulation_id}]
              </div>
            )}
          </div>

          <div className="sf-panel">
            <h2>📈 Live MARL Telemetry</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1rem' }}>
              Poll the Reinforcement Learning engine to see how the swarm is adapting.
            </p>
            <button onClick={handlePollTelemetry} className="sf-btn" disabled={loading || !activeSimId} style={{ background: '#333', color: '#fff', marginTop: '0' }}>
              Poll Swarm Behavior
            </button>

            {telemetry && (
              <div className="sf-telemetry-grid">
                <div className="sf-metric-box">
                  <div className="sf-metric-label">Coordination Score</div>
                  <div className="sf-metric-value">{telemetry.coordination_score.toFixed(2)}</div>
                </div>
                <div className="sf-metric-box">
                  <div className="sf-metric-value">{telemetry.mutation_velocity.toFixed(2)}</div>
                  <div className="sf-metric-label" style={{marginTop: '0.5rem', marginBottom: 0}}>Mutation Velocity</div>
                </div>
                <div className="sf-pivot-box">
                  <div className="sf-metric-label">Predicted Infrastructure Pivot</div>
                  <div className="sf-pivot-target">{telemetry.predicted_pivot_target}</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Defense */}
        <div>
          <div className="sf-panel">
            <h2>🛡️ Deploy Counter-Swarm</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Release defensive AI agents to intercept and neutralize the attacking swarm based on their current telemetry.
            </p>
            <form onSubmit={handleDeployDefense}>
              <div className="sf-form-group">
                <label>Counter-Measure Strategy</label>
                <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                  <option value="HONEYPOT_DECOY">Honeypot Decoy Swarm</option>
                  <option value="SIGNAL_JAMMING">Agent Signal Jamming</option>
                  <option value="QUARANTINE_NET">Dynamic Quarantine Net</option>
                </select>
              </div>
              <button type="submit" className="sf-btn defend" disabled={loading || !activeSimId}>Deploy Defense Swarm</button>
            </form>

            {defenseResult && (
              <div className="sf-neutral-result">
                <div style={{ color: '#888', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Neutralization Effectiveness</div>
                <div className="sf-neutral-percent">{defenseResult.neutralization_percentage}%</div>
                <div style={{ color: defenseResult.swarm_deactivated ? '#00ff88' : '#ffaa00' }}>
                  {defenseResult.swarm_deactivated ? 'Swarm successfully deactivated.' : 'Swarm partially active. Recommend secondary deployment.'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
