import React, { useState } from 'react';
import './GridShieldDashboard.css';

interface ScadaResult {
  device_id: string;
  is_anomalous: boolean;
  flag_reason: string;
}

interface PhysicalResult {
  target_component: string;
  kinetic_damage_probability: number;
  structural_integrity_warning: string;
}

interface ResilienceResult {
  grid_sector: string;
  load_shedding_percentage: number;
  islanding_required: boolean;
  action_plan: string;
}

interface ForecastResult {
  region: string;
  five_year_risk_score: number;
  primary_threat_vector: string;
}

export default function GridShieldDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // SCADA State
  const [deviceId, setDeviceId] = useState('PLC-99');
  const [protocol, setProtocol] = useState('Modbus');
  const [payload, setPayload] = useState('UNAUTH_WRITE_REG_4001');
  const [frequency, setFrequency] = useState<number>(150.0);
  const [scadaResult, setScadaResult] = useState<ScadaResult | null>(null);

  // Physical State
  const [targetComponent, setTargetComponent] = useState('Turbine-A');
  const [injectedRpm, setInjectedRpm] = useState<number>(4500.0);
  const [normalRpm, setNormalRpm] = useState<number>(3000.0);
  const [physicalResult, setPhysicalResult] = useState<PhysicalResult | null>(null);

  // Resilience State
  const [sector, setSector] = useState('Sector-7G');
  const [currentLoad, setCurrentLoad] = useState<number>(500.0);
  const [compromisedNodes, setCompromisedNodes] = useState<number>(8);
  const [resilienceResult, setResilienceResult] = useState<ResilienceResult | null>(null);

  // Forecast State
  const [region, setRegion] = useState('US-EAST');
  const [iotLevel, setIotLevel] = useState<number>(8.5);
  const [incidents, setIncidents] = useState<number>(5);
  const [forecastResult, setForecastResult] = useState<ForecastResult | null>(null);

  const handleAnalyzeScada = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setScadaResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/gridshield/analyze-scada', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: deviceId,
          protocol: protocol,
          packet_payload: payload,
          frequency_hz: frequency
        })
      });
      if (!response.ok) throw new Error('SCADA analysis failed');
      setScadaResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulatePhysical = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPhysicalResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/gridshield/simulate-physical', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_component: targetComponent,
          injected_rpm: injectedRpm,
          normal_operating_rpm: normalRpm
        })
      });
      if (!response.ok) throw new Error('Physical simulation failed');
      setPhysicalResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanResilience = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResilienceResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/gridshield/plan-resilience', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grid_sector: sector,
          current_load_mw: currentLoad,
          compromised_nodes: compromisedNodes
        })
      });
      if (!response.ok) throw new Error('Resilience planning failed');
      setResilienceResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForecastThreat = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setForecastResult(null);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/gridshield/forecast-threat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          region: region,
          iot_integration_level: iotLevel,
          past_incidents_count: incidents
        })
      });
      if (!response.ok) throw new Error('Threat forecasting failed');
      setForecastResult(await response.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="gridshield-dashboard">
      <header className="gs-header">
        <h1>⚡ GridShield Architect</h1>
        <p>Critical Infrastructure SCADA Defense, Kinetic Simulation & Grid Resilience</p>
      </header>

      {error && <div className="gs-alert">{error}</div>}

      <div className="gs-grid">
        {/* Left Column */}
        <div>
          <div className="gs-panel" style={{ marginBottom: '2rem' }}>
            <h2>📡 SCADA/ICS Protocol Analysis</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Monitor OT networks for unauthorized writes and high-frequency polling anomalies.
            </p>
            <form onSubmit={handleAnalyzeScada}>
              <div className="gs-form-group">
                <label>Device ID</label>
                <input type="text" value={deviceId} onChange={(e) => setDeviceId(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="gs-form-group">
                  <label>Protocol</label>
                  <select value={protocol} onChange={(e) => setProtocol(e.target.value)}>
                    <option value="Modbus">Modbus TCP</option>
                    <option value="DNP3">DNP3</option>
                    <option value="IEC-104">IEC-104</option>
                  </select>
                </div>
                <div className="gs-form-group">
                  <label>Polling Freq (Hz)</label>
                  <input type="number" step="0.1" value={frequency} onChange={(e) => setFrequency(parseFloat(e.target.value))} required />
                </div>
              </div>
              <div className="gs-form-group">
                <label>Packet Payload Hex/String</label>
                <textarea rows={2} value={payload} onChange={(e) => setPayload(e.target.value)} required />
              </div>
              <button type="submit" className="gs-btn" disabled={loading}>Analyze SCADA Traffic</button>
            </form>

            {scadaResult && (
              <div className={`gs-result-box ${scadaResult.is_anomalous ? 'danger' : 'nominal'}`}>
                <div className="gs-result-title" style={{ color: scadaResult.is_anomalous ? '#ff4444' : '#00ffcc' }}>
                  {scadaResult.is_anomalous ? 'OT ANOMALY DETECTED' : 'PROTOCOL NOMINAL'}
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  {scadaResult.flag_reason}
                </div>
              </div>
            )}
          </div>

          <div className="gs-panel">
            <h2>💥 Cyber-Physical Simulation (Kinetic Impact)</h2>
            <form onSubmit={handleSimulatePhysical}>
              <div className="gs-form-group">
                <label>Target Component</label>
                <input type="text" value={targetComponent} onChange={(e) => setTargetComponent(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="gs-form-group">
                  <label>Injected RPM</label>
                  <input type="number" step="0.1" value={injectedRpm} onChange={(e) => setInjectedRpm(parseFloat(e.target.value))} required />
                </div>
                <div className="gs-form-group">
                  <label>Normal RPM</label>
                  <input type="number" step="0.1" value={normalRpm} onChange={(e) => setNormalRpm(parseFloat(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="gs-btn" disabled={loading} style={{ background: '#ff4444', color: '#fff' }}>Simulate Kinetic Damage</button>
            </form>

            {physicalResult && (
              <div className={`gs-result-box ${physicalResult.kinetic_damage_probability > 50 ? 'danger' : 'warning'}`}>
                <div className="gs-result-title" style={{ color: physicalResult.kinetic_damage_probability > 50 ? '#ff4444' : '#ffaa00' }}>
                  DAMAGE PROBABILITY: {physicalResult.kinetic_damage_probability.toFixed(1)}%
                </div>
                <div style={{ color: '#e0e0e0', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  {physicalResult.structural_integrity_warning}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="gs-panel" style={{ marginBottom: '2rem' }}>
            <h2>🛡️ Grid Resilience & Blackout Planning</h2>
            <form onSubmit={handlePlanResilience}>
              <div className="gs-form-group">
                <label>Grid Sector</label>
                <input type="text" value={sector} onChange={(e) => setSector(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="gs-form-group">
                  <label>Current Load (MW)</label>
                  <input type="number" step="0.1" value={currentLoad} onChange={(e) => setCurrentLoad(parseFloat(e.target.value))} required />
                </div>
                <div className="gs-form-group">
                  <label>Compromised Nodes</label>
                  <input type="number" value={compromisedNodes} onChange={(e) => setCompromisedNodes(parseInt(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="gs-btn" disabled={loading} style={{ background: '#4facfe', color: '#fff' }}>Calculate Blackout Mitigation</button>
            </form>

            {resilienceResult && (
              <div className={`gs-result-box ${resilienceResult.islanding_required ? 'danger' : 'info'}`}>
                <div className="gs-result-title" style={{ color: resilienceResult.islanding_required ? '#ff4444' : '#4facfe' }}>
                  {resilienceResult.islanding_required ? 'ISLANDING REQUIRED' : 'GRID STABLE'}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                  <div>
                    <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Load Shedding</div>
                    <div style={{ color: '#e0e0e0', fontWeight: 'bold' }}>{resilienceResult.load_shedding_percentage.toFixed(1)}%</div>
                  </div>
                  <div style={{ gridColumn: '1 / -1', color: '#e0e0e0', fontSize: '0.9rem' }}>
                    {resilienceResult.action_plan}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="gs-panel">
            <h2>📈 Long-Term Threat Forecasting</h2>
            <form onSubmit={handleForecastThreat}>
              <div className="gs-form-group">
                <label>Geographic Region</label>
                <input type="text" value={region} onChange={(e) => setRegion(e.target.value)} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="gs-form-group">
                  <label>IoT Integration Level (0-10)</label>
                  <input type="number" step="0.1" value={iotLevel} onChange={(e) => setIotLevel(parseFloat(e.target.value))} required />
                </div>
                <div className="gs-form-group">
                  <label>Past 5-Yr Incidents</label>
                  <input type="number" value={incidents} onChange={(e) => setIncidents(parseInt(e.target.value))} required />
                </div>
              </div>
              <button type="submit" className="gs-btn" disabled={loading} style={{ background: '#333', color: '#ffd700', border: '1px solid #ffd700' }}>Generate 5-Year Forecast</button>
            </form>

            {forecastResult && (
              <div className="gs-result-box warning">
                <div className="gs-result-title" style={{ color: '#ffaa00' }}>
                  5-YEAR RISK SCORE: {forecastResult.five_year_risk_score.toFixed(1)}
                </div>
                <div style={{ marginTop: '0.5rem' }}>
                  <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase' }}>Primary Threat Vector</div>
                  <div style={{ color: '#e0e0e0', fontSize: '0.9rem' }}>{forecastResult.primary_threat_vector}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
