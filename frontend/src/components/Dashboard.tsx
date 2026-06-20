import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RadarChart } from './RadarChart';
import { BarChart } from './BarChart';
import './Dashboard.css';

interface DashboardStats {
  platform: string;
  generated_at: string;
  threats_detected: number;
  scenarios_run: number;
  evidence_items: number;
  bsa_certs_issued: number;
  active_modules: number;
  backend_uptime_hours: number;
  threat_trend: Array<{ hour: string; count: number }>;
  top_threat_actors: Array<{ name: string; incidents: number; severity: string }>;
  module_usage: Record<string, number>;
}

export const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/api/dashboard/stats')
      .then((res) => {
        if (!res.ok) throw new Error('API down');
        return res.json();
      })
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching dashboard stats:', err);
        setLoading(false);
      });
  }, []);

  return (
    <section className="animate-in" style={{ padding: '24px 0' }}>
      <div className="dashboard-header">
        <h1 className="section-title">
          <span className="icon">📊</span>
          <span className="text-gradient">Threat Intelligence Center</span>
        </h1>
        <p className="section-subtitle">Real-time digital forensics and BSA compliance reporting platform</p>
      </div>

      {loading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <span>Synchronizing with secure backend server...</span>
        </div>
      )}

      {!loading && !stats && (
        <div className="empty-state">
          <div className="icon">⚠️</div>
          <h3>System Offline</h3>
          <p>Failed to establish a secure handshake with the CyberThreatForge node server.</p>
        </div>
      )}

      {stats && (
        <>
          {/* STATS COUNTER GRID */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Threats Ingested</div>
              <div className="stat-value">{stats.threats_detected}</div>
              <div className="stat-detail">Total active IOC threats parsed</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Scenarios Run</div>
              <div className="stat-value">{stats.scenarios_run}</div>
              <div className="stat-detail">Threat simulation timelines executed</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Forensic Artifacts</div>
              <div className="stat-value">{stats.evidence_items}</div>
              <div className="stat-detail">Database, media, & hardware files</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">BSA Certificates</div>
              <div className="stat-value">{stats.bsa_certs_issued}</div>
              <div className="stat-detail">Section 63 compliance certificates</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Active Modules</div>
              <div className="stat-value">{stats.active_modules}</div>
              <div className="stat-detail">Vulnerability & forensic decoders</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">System Uptime</div>
              <div className="stat-value">{stats.backend_uptime_hours}h</div>
              <div className="stat-detail">Continuous secure session time</div>
            </div>
          </div>

          {/* MAIN CHARTS GRID */}
          <div className="chart-grid">
            <div className="chart-card">
              <h3>
                <span className="dot"></span>
                Module Forensic Affinity
              </h3>
              <RadarChart data={stats.module_usage} />
            </div>

            <div className="chart-card">
              <h3>
                <span className="dot"></span>
                Threat Activity Trend (24h)
              </h3>
              <BarChart trendData={stats.threat_trend} />
            </div>
          </div>

          {/* DUAL GRID: ACTORS & ACTIONS */}
          <div className="dashboard-grid">
            <div className="threat-actors-panel">
              <h3>Active Threat Group Profile</h3>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Actor / Threat Profile</th>
                    <th>Targeted Incidents</th>
                    <th>Risk Rating</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.top_threat_actors.map((actor, idx) => (
                    <tr key={idx}>
                      <td className="mono">{actor.name}</td>
                      <td>{actor.incidents}</td>
                      <td>
                        <span className={`badge badge-${actor.severity.toLowerCase()}`}>
                          {actor.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="threat-actors-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <h3>Forensic Actions</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  Execute automated tool chains to inspect mobile targets, analyze deepfakes, inspect hardware, and certify under Bharatiya Sakshya Adhiniyam (BSA).
                </p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '10px' }}>
                <button className="action-btn" onClick={() => navigate('/investigation')}>
                  <span className="action-icon">🔬</span>
                  Launch Forensic Lab Range
                </button>
                <button className="action-btn" onClick={() => navigate('/reports')}>
                  <span className="action-icon">📋</span>
                  Draft CERT-IN Incident Report
                </button>
                <button className="action-btn" onClick={() => navigate('/analytics')}>
                  <span className="action-icon">🌐</span>
                  Explore Threat Intelligence Map
                </button>
              </div>
            </div>
          </div>

          {/* ADVANCED MODULES GRID */}
          <div className="advanced-modules-panel" style={{ marginTop: '24px' }}>
            <h3>Advanced Security Modules (Batch 1-4)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginTop: '16px' }}>
              <button className="action-btn" onClick={() => navigate('/modeldefender')}>ModelDefender</button>
              <button className="action-btn" onClick={() => navigate('/firmwareguard')}>FirmwareGuard</button>
              <button className="action-btn" onClick={() => navigate('/psyopsforge')}>PsyOpsForge</button>
              <button className="action-btn" onClick={() => navigate('/correlix')}>Correlix</button>
              <button className="action-btn" onClick={() => navigate('/collabspace')}>CollabSpace</button>
              <button className="action-btn" onClick={() => navigate('/learnforge')}>LearnForge</button>
              <button className="action-btn" onClick={() => navigate('/behavix-new')}>Behavix</button>
              <button className="action-btn" onClick={() => navigate('/undergroundforge')}>UndergroundForge</button>
              <button className="action-btn" onClick={() => navigate('/zerodayforge')}>ZeroDayForge</button>
              <button className="action-btn" onClick={() => navigate('/linguaguard')}>LinguaGuard</button>
              <button className="action-btn" onClick={() => navigate('/anomalymaster')}>AnomalyMaster</button>
              <button className="action-btn" onClick={() => navigate('/voiceguard')}>VoiceGuard</button>
              <button className="action-btn" onClick={() => navigate('/smartcityguard')}>SmartCityGuard</button>
              <button className="action-btn" onClick={() => navigate('/defiguard')}>DeFiGuard</button>
              <button className="action-btn" onClick={() => navigate('/adversarydefender')}>AdversaryDefender</button>
              <button className="action-btn" onClick={() => navigate('/sovereignguard')}>SovereignGuard</button>
              <button className="action-btn" onClick={() => navigate('/legacyshield')}>LegacyShield</button>
            </div>
          </div>
        </>
      )}
    </section>
  );
};
