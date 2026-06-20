import React, { useState } from 'react';
import './OmniSimulatorDashboard.css';

interface ScenarioResult {
  scenario_id: string;
  name: string;
  status: string;
  global_resilience_score: number;
}

interface EventTriggerResult {
  event_id: string;
  source_module: string;
  event_description: string;
  cascades_triggered: number;
  new_resilience_score: number;
}

interface GlobalStateResponse {
  scenario_id: string;
  status: string;
  global_resilience_score: number;
  total_events: number;
  total_cascades: number;
}

const MODULES = [
  "SupplyChain", "InsiderShield", "OSINT", "ResponseForge", "HardwareForensix", 
  "Training", "EvolvoAI", "CollabGuard", "RedTeam", "RansomGuard", 
  "CloudForensix", "QuantumSafe", "NetGuard", "EthicsForge", "ResilientForge", 
  "SwarmForge", "NeuroGuard", "SpaceGuard", "ClimateShield", "NanoQuantum", 
  "InnovateGuard", "MetaForge", "DroneGuard", "MetaGuard", "FinGuard", 
  "HumanForge", "GridShield", "PromptDefender", "GlobalJurix", "ZeroTrustForge"
];

export default function OmniSimulatorDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scenario State
  const [scenarioId, setScenarioId] = useState('SCENARIO-' + Math.floor(Math.random() * 10000));
  const [scenarioName, setScenarioName] = useState('Operation Midnight: Quantum Grid Collapse');
  const [scenarioDesc, setScenarioDesc] = useState('Global multi-stage cyber warfare simulation spanning all 30 modules.');
  const [activeScenario, setActiveScenario] = useState<ScenarioResult | null>(null);

  // Event State
  const [sourceModule, setSourceModule] = useState('SpaceGuard');
  const [eventDesc, setEventDesc] = useState('Satellite Command & Control link hijacked by rogue nation state.');
  const [severity, setSeverity] = useState('CRITICAL');
  const [lastEvent, setLastEvent] = useState<EventTriggerResult | null>(null);

  // Global State
  const [globalState, setGlobalState] = useState<GlobalStateResponse | null>(null);

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/omnisimulator/launch-scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: scenarioId,
          name: scenarioName,
          description: scenarioDesc
        })
      });
      if (!response.ok) throw new Error('Failed to launch scenario');
      const data = await response.json();
      setActiveScenario(data);
      pollGlobalState(data.scenario_id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeScenario) {
      setError("Please launch a scenario first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/omnisimulator/trigger-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: activeScenario.scenario_id,
          source_module: sourceModule,
          event_description: eventDesc,
          severity: severity
        })
      });
      if (!response.ok) throw new Error('Failed to trigger event');
      const data = await response.json();
      setLastEvent(data);
      pollGlobalState(activeScenario.scenario_id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const pollGlobalState = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/omnisimulator/global-state/${id}`);
      if (response.ok) {
        setGlobalState(await response.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="omni-dashboard">
      <header className="omni-header">
        <h1>🌐 OmniForge Simulator: War Room</h1>
        <p>Master Orchestration Layer for 30 Integrated Security Domains</p>
      </header>

      {error && <div className="omni-alert">{error}</div>}

      <div className="omni-grid">
        {/* Left Column: Control Panel */}
        <div>
          {!activeScenario ? (
            <div className="omni-panel" style={{ marginBottom: '2rem' }}>
              <h2>🚀 Launch Global Scenario</h2>
              <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Initialize the OmniSimulator and bind all 30 modules to a unified timeline.
              </p>
              <form onSubmit={handleLaunch}>
                <div className="omni-form-group">
                  <label>Scenario ID</label>
                  <input type="text" value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} required />
                </div>
                <div className="omni-form-group">
                  <label>Scenario Name</label>
                  <input type="text" value={scenarioName} onChange={(e) => setScenarioName(e.target.value)} required />
                </div>
                <div className="omni-form-group">
                  <label>Description</label>
                  <textarea value={scenarioDesc} onChange={(e) => setScenarioDesc(e.target.value)} rows={3} required />
                </div>
                <button type="submit" className="omni-btn" disabled={loading}>Initialize OmniSimulator</button>
              </form>
            </div>
          ) : (
            <div className="omni-panel" style={{ marginBottom: '2rem', border: '1px solid #00ffcc' }}>
              <h2 style={{ color: '#00ffcc' }}>🟢 Scenario Active: {activeScenario.name}</h2>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                ID: {activeScenario.scenario_id} <br/>
                All 30 modules online and listening for events.
              </div>
            </div>
          )}

          <div className="omni-panel" style={{ opacity: activeScenario ? 1 : 0.5, pointerEvents: activeScenario ? 'auto' : 'none' }}>
            <h2>⚡ Trigger Module Event</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Inject an attack into a specific module and watch the CascadeEngine calculate collateral damage.
            </p>
            <form onSubmit={handleTrigger}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="omni-form-group">
                  <label>Source Module</label>
                  <select value={sourceModule} onChange={(e) => setSourceModule(e.target.value)}>
                    {MODULES.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div className="omni-form-group">
                  <label>Severity</label>
                  <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>
              <div className="omni-form-group">
                <label>Event Description</label>
                <input type="text" value={eventDesc} onChange={(e) => setEventDesc(e.target.value)} required />
              </div>
              <button type="submit" className="omni-btn" disabled={loading} style={{ background: '#ff3366' }}>Inject Threat</button>
            </form>

            {lastEvent && (
              <div className="omni-result-box warning" style={{ marginTop: '1.5rem' }}>
                <div className="omni-result-title" style={{ color: '#ffaa00' }}>
                  EVENT {lastEvent.event_id} INJECTED
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  <strong>Source:</strong> {lastEvent.source_module} <br/>
                  <strong>Cascades Triggered:</strong> {lastEvent.cascades_triggered} downstream module breaches calculated. <br/>
                  <strong>Resilience Drop:</strong> Score updated to {lastEvent.new_resilience_score.toFixed(1)}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Global View */}
        <div>
          <div className="omni-panel" style={{ height: '100%' }}>
            <h2>🌍 Global Platform Resilience</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '2rem' }}>
              Aggregated health of all 30 Amroha01 modules.
            </p>

            <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
              <div style={{ fontSize: '4rem', fontWeight: 'bold', color: (globalState?.global_resilience_score || 100) < 50 ? '#ff4444' : ((globalState?.global_resilience_score || 100) < 80 ? '#ffaa00' : '#00ffcc') }}>
                {(globalState?.global_resilience_score || 100).toFixed(1)}%
              </div>
              <div style={{ color: '#888', textTransform: 'uppercase', letterSpacing: '2px' }}>
                System Integrity
              </div>
              
              <div className="resilience-meter" style={{ marginTop: '1.5rem' }}>
                <div 
                  className="resilience-fill" 
                  style={{ 
                    width: `${globalState?.global_resilience_score || 100}%`,
                    background: (globalState?.global_resilience_score || 100) < 50 ? '#ff4444' : ((globalState?.global_resilience_score || 100) < 80 ? '#ffaa00' : '#00ffcc')
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: '#111', padding: '1.5rem', borderRadius: '8px' }}>
              <div>
                <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Active Scenario</div>
                <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '1.1rem' }}>{globalState?.scenario_id || 'NONE'}</div>
              </div>
              <div>
                <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Modules Engaged</div>
                <div style={{ color: '#00ffcc', fontWeight: 'bold', fontSize: '1.1rem' }}>30 / 30</div>
              </div>
              <div>
                <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Primary Events</div>
                <div style={{ color: '#ffaa00', fontWeight: 'bold', fontSize: '1.1rem' }}>{globalState?.total_events || 0}</div>
              </div>
              <div>
                <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Cascading Breaches</div>
                <div style={{ color: '#ff4444', fontWeight: 'bold', fontSize: '1.1rem' }}>{globalState?.total_cascades || 0}</div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
