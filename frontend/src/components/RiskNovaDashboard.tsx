import React, { useState } from 'react';
import './RiskNovaDashboard.css';

interface TechProfile {
  tech_name: string;
  sub_category: string;
  adoption_phase: string;
}

interface RiskAssessment {
  cyber_risk_score: number;
  physical_risk_score: number;
  operational_risk_score: number;
  composite_score: number;
}

interface RiskScenario {
  scenario_name: string;
  description: string;
  probability: number;
  impact_level: string;
  timeframe_years: number;
}

interface MitigationRoadmap {
  step_order: number;
  action_item: string;
  resource_requirement: string;
  status: string;
}

export const RiskNovaDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form State
  const [techName, setTechName] = useState('Autonomous LLM Agents');
  const [subCategory, setSubCategory] = useState('Generative AI');
  const [adoptionPhase, setAdoptionPhase] = useState('EarlyAdoption');
  
  // Results State
  const [_profile, setProfile] = useState<TechProfile | null>(null);
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [scenarios, setScenarios] = useState<RiskScenario[]>([]);
  const [roadmaps, setRoadmaps] = useState<MitigationRoadmap[]>([]);

  const handleAssess = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = {
        tech_name: techName,
        sub_category: subCategory,
        adoption_phase: adoptionPhase
      };

      const res = await fetch('http://localhost:8000/api/risknova/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error('Failed to run RiskNova assessment');
      
      const data = await res.json();
      setProfile(data.profile);
      setAssessment(data.assessment);
      setScenarios(data.scenarios);
      setRoadmaps(data.roadmaps);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="risknova-dashboard">
      <div className="risknova-header">
        <h2>RiskNova Architect</h2>
        <p>Proactive Emerging Technology Risk Assessment</p>
      </div>

      <div className="risknova-content">
        {/* Input Form */}
        <div className="risknova-panel input-panel">
          <h3>Target Technology</h3>
          <form onSubmit={handleAssess}>
            <div className="form-group">
              <label>Technology Area</label>
              <select value={techName} onChange={(e) => setTechName(e.target.value)}>
                <option value="Autonomous LLM Agents">Autonomous LLM Agents</option>
                <option value="Quantum Cryptography">Quantum Cryptography</option>
                <option value="CRISPR Synthetic Biology">CRISPR Synthetic Biology</option>
                <option value="LEO Satellite Swarm">LEO Satellite Swarm</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Sub-Category</label>
              <input type="text" value={subCategory} onChange={(e) => setSubCategory(e.target.value)} />
            </div>

            <div className="form-group">
              <label>Adoption Phase</label>
              <select value={adoptionPhase} onChange={(e) => setAdoptionPhase(e.target.value)}>
                <option value="R&D">Research & Development</option>
                <option value="EarlyAdoption">Early Adoption</option>
                <option value="Mainstream">Mainstream</option>
              </select>
            </div>

            <button type="submit" className="assess-btn" disabled={loading}>
              {loading ? 'Running Simulations...' : 'Generate Risk Forecast'}
            </button>
          </form>
          {error && <div className="error-box">{error}</div>}
        </div>

        {/* Results */}
        {assessment && (
          <div className="risknova-results">
            <div className="risknova-panel score-panel">
              <h3>Multi-Dimensional Risk Score</h3>
              <div className="score-bars">
                <div className="score-item">
                  <span>Cyber Risk</span>
                  <div className="bar-bg">
                    <div className="bar-fill cyber" style={{ width: `${assessment.cyber_risk_score * 100}%` }}></div>
                  </div>
                  <span>{(assessment.cyber_risk_score * 100).toFixed(1)}%</span>
                </div>
                <div className="score-item">
                  <span>Physical Risk</span>
                  <div className="bar-bg">
                    <div className="bar-fill physical" style={{ width: `${assessment.physical_risk_score * 100}%` }}></div>
                  </div>
                  <span>{(assessment.physical_risk_score * 100).toFixed(1)}%</span>
                </div>
                <div className="score-item">
                  <span>Operational Risk</span>
                  <div className="bar-bg">
                    <div className="bar-fill operational" style={{ width: `${assessment.operational_risk_score * 100}%` }}></div>
                  </div>
                  <span>{(assessment.operational_risk_score * 100).toFixed(1)}%</span>
                </div>
              </div>
              <div className="composite-score">
                <h4>Composite Threat Vector</h4>
                <div className="huge-score">{(assessment.composite_score * 100).toFixed(1)}</div>
              </div>
            </div>

            <div className="risknova-panel scenario-panel">
              <h3>Forecasted Scenarios</h3>
              {scenarios.map((s, idx) => (
                <div key={idx} className={`scenario-card impact-${s.impact_level.toLowerCase()}`}>
                  <h4>{s.scenario_name}</h4>
                  <p>{s.description}</p>
                  <div className="scenario-meta">
                    <span className="badge">Prob: {(s.probability * 100).toFixed(0)}%</span>
                    <span className="badge">T-{s.timeframe_years} Years</span>
                    <span className="badge">{s.impact_level} Impact</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="risknova-panel roadmap-panel">
              <h3>Mitigation Roadmap</h3>
              <ul className="roadmap-list">
                {roadmaps.map((r, idx) => (
                  <li key={idx} className="roadmap-item">
                    <div className="step-number">{r.step_order}</div>
                    <div className="step-content">
                      <p>{r.action_item}</p>
                      <span className={`resource-badge res-${r.resource_requirement.toLowerCase()}`}>
                        {r.resource_requirement} Resource
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskNovaDashboard;
