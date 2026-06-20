import React, { useState } from 'react';
import './ClimateShieldDashboard.css';

interface InfraAttackResult {
  infrastructure_type: string;
  cascading_impact_score: number;
  analysis_details: string;
}

interface ClimateSimResult {
  manipulation_vector: string;
  projected_years: number;
  ecological_damage_index: number;
  economic_impact_trillions: number;
  details: string;
}

interface ResiliencePlanResult {
  scenario_trigger: string;
  recovery_strategy: string;
  estimated_recovery_days: number;
}

export default function ClimateShieldDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Infra State
  const [infraType, setInfraType] = useState('WATER');
  const [weatherEvent, setWeatherEvent] = useState('DROUGHT');
  const [cyberVector, setCyberVector] = useState('SCADA_HIJACK');
  const [infraResult, setInfraResult] = useState<InfraAttackResult | null>(null);

  // Geo State
  const [manipulationVector, setManipulationVector] = useState('CLOUD_SEEDING_HIJACK');
  const [projectedYears, setProjectedYears] = useState<number>(50);
  const [geoResult, setGeoResult] = useState<ClimateSimResult | null>(null);

  // Plan State
  const [scenarioTrigger, setScenarioTrigger] = useState('WATER_INFRASTRUCTURE_COLLAPSE');
  const [severityScore, setSeverityScore] = useState<number>(9.5);
  const [planResult, setPlanResult] = useState<ResiliencePlanResult | null>(null);

  const handleInfraAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setInfraResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/climateshield/simulate-infra-attack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          infrastructure_type: infraType,
          weather_event: weatherEvent,
          cyber_attack_vector: cyberVector
        })
      });
      if (!response.ok) throw new Error('Simulation failed');
      setInfraResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGeoSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setGeoResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/climateshield/simulate-climate-manipulation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          manipulation_vector: manipulationVector,
          projected_years: projectedYears
        })
      });
      if (!response.ok) throw new Error('Simulation failed');
      setGeoResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPlanResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/climateshield/generate-resilience-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_trigger: scenarioTrigger,
          severity_score: severityScore
        })
      });
      if (!response.ok) throw new Error('Plan generation failed');
      setPlanResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="climateshield-dashboard">
      <header className="cs-header">
        <h1>🌍 ClimateShield Architect</h1>
        <p>Geo-Engineering Threat Modeling & Critical Infrastructure Resilience</p>
      </header>

      {error && <div className="cs-alert">{error}</div>}

      <div className="cs-grid">
        {/* Left Column */}
        <div>
          <div className="cs-panel" style={{ marginBottom: '2rem' }}>
            <h2>🌪️ Hybrid Climate-Cyber Attack Modeler</h2>
            <form onSubmit={handleInfraAnalyze}>
              <div className="cs-form-group">
                <label>Target Infrastructure</label>
                <select value={infraType} onChange={(e) => setInfraType(e.target.value)}>
                  <option value="WATER">Water Supply & Desalination</option>
                  <option value="POWER">Power Grid (Cooling Systems)</option>
                  <option value="AGRICULTURE">Agricultural Dams & Irrigation</option>
                </select>
              </div>
              <div className="cs-form-group">
                <label>Concurrent Weather Event</label>
                <select value={weatherEvent} onChange={(e) => setWeatherEvent(e.target.value)}>
                  <option value="DROUGHT">Severe Drought</option>
                  <option value="HEATWAVE">Heatwave</option>
                  <option value="FLOOD">Torrential Flooding</option>
                </select>
              </div>
              <div className="cs-form-group">
                <label>Cyber Attack Vector</label>
                <input type="text" value={cyberVector} onChange={(e) => setCyberVector(e.target.value)} required />
              </div>
              <button type="submit" className="cs-btn" disabled={loading}>Run Attack Simulation</button>
            </form>

            {infraResult && (
              <div className="cs-infra-result">
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Cascading Impact Score</div>
                  <div style={{ color: '#ff4444', fontWeight: 'bold', fontSize: '2rem' }}>
                    {infraResult.cascading_impact_score.toFixed(1)} / 10.0
                  </div>
                </div>
                <div>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Analysis Details</div>
                  <div style={{ color: '#fff' }}>{infraResult.analysis_details}</div>
                </div>
              </div>
            )}
          </div>

          <div className="cs-panel">
            <h2>🏗️ Autonomous Resilience Planner</h2>
            <form onSubmit={handlePlanGenerate}>
              <div className="cs-form-group">
                <label>Scenario Trigger</label>
                <input type="text" value={scenarioTrigger} onChange={(e) => setScenarioTrigger(e.target.value)} required />
              </div>
              <div className="cs-form-group">
                <label>Impact Severity Score (0-10)</label>
                <input type="number" step="0.1" value={severityScore} onChange={(e) => setSeverityScore(parseFloat(e.target.value))} required />
              </div>
              <button type="submit" className="cs-btn" disabled={loading} style={{ background: '#333', color: '#fff', border: '1px solid #00ffaa' }}>Generate Blueprint</button>
            </form>

            {planResult && (
              <div className="cs-plan-result">
                <div style={{ color: '#00ffaa', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                  RECOVERY PLAN DEPLOYED
                </div>
                <div style={{ color: '#e0e0e0', marginBottom: '1rem' }}>{planResult.recovery_strategy}</div>
                <div style={{ color: '#888', fontSize: '0.9rem' }}>
                  Estimated Recovery Time: <strong style={{ color: '#fff' }}>{planResult.estimated_recovery_days} days</strong>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="cs-panel">
            <h2>🧪 50+ Year Geo-Engineering Projections</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Project the devastating long-term impacts of weaponized climate manipulation vectors by rogue AI or state actors.
            </p>
            <form onSubmit={handleGeoSimulate}>
              <div className="cs-form-group">
                <label>Manipulation Vector</label>
                <select value={manipulationVector} onChange={(e) => setManipulationVector(e.target.value)}>
                  <option value="CLOUD_SEEDING_HIJACK">Weaponized Cloud Seeding</option>
                  <option value="ROGUE_AEROSOL">Rogue Aerosol Injection</option>
                </select>
              </div>
              <div className="cs-form-group">
                <label>Projection Timeline (Years)</label>
                <input type="number" value={projectedYears} onChange={(e) => setProjectedYears(parseInt(e.target.value))} required />
              </div>
              <button type="submit" className="cs-btn" disabled={loading} style={{ background: '#ff4444', color: '#fff' }}>Project Long-Term Damage</button>
            </form>

            {geoResult && (
              <div className="cs-sim-result">
                <div style={{ color: '#fff', marginBottom: '1.5rem', fontStyle: 'italic' }}>
                  "{geoResult.details}"
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Ecological Damage Index</div>
                    <div style={{ color: '#ff4444', fontWeight: 'bold', fontSize: '1.5rem' }}>
                      {geoResult.ecological_damage_index.toFixed(1)} / 10.0
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Economic Impact</div>
                    <div style={{ color: '#ffcc00', fontWeight: 'bold', fontSize: '1.5rem' }}>
                      ${geoResult.economic_impact_trillions.toFixed(1)} Trillion
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
