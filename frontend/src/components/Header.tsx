import { NavLink } from 'react-router-dom';
import './Header.css';

export const Header = () => (
  <header className="header">
    <div className="header-inner">
      <div className="header-brand">
        <span className="header-logo">🛡️</span>
        <span className="header-title">CyberThreatForge</span>
        <span className="header-version">v2.0</span>
      </div>

      <nav className="header-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📊</span>
          <span>Dashboard</span>
        </NavLink>
        <NavLink to="/investigation" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🔬</span>
          <span>Investigation</span>
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🌐</span>
          <span>Intel Map</span>
        </NavLink>
        <NavLink to="/reports" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📋</span>
          <span>Reports</span>
        </NavLink>
        <NavLink to="/research" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📚</span>
          <span>Research</span>
        </NavLink>
        <NavLink to="/activity" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📡</span>
          <span>Activity</span>
        </NavLink>
        <NavLink to="/behavioral" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🧠</span>
          <span>Behavioral</span>
        </NavLink>
        <NavLink to="/metaverse" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🪐</span>
          <span>Metaverse</span>
                  </NavLink>
          <NavLink
            to="/supplyguard"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🛡️</span>
            <span>Supply Guard</span>
          </NavLink>
          <NavLink
            to="/osint"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🕵️‍♀️</span>
            <span>OSINT</span>
          </NavLink>
          <NavLink to="/responseforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">⚔️</span>
            <span>Response</span>
          </NavLink>
          <NavLink to="/hardwareforensix" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">💻</span>
            <span>Hardware</span>
          </NavLink>
          <NavLink to="/evolvoai" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🧬</span>
            <span>EvolvoAI</span>
          </NavLink>
          <NavLink to="/collabguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🤝</span>
            <span>CollabGuard</span>
          </NavLink>
          <NavLink to="/ransomguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">💸</span>
            <span>RansomGuard</span>
          </NavLink>
          <NavLink to="/cloudforensix" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">☁️</span>
            <span>CloudForensix</span>
          </NavLink>
          <NavLink to="/quantumsafe" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">⚛️</span>
            <span>QuantumSafe</span>
          </NavLink>
          <NavLink to="/commforensix" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🔐</span>
            <span>CommForensix</span>
          </NavLink>
          <NavLink to="/netguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🌐</span>
            <span>NetGuard</span>
          </NavLink>
          <NavLink to="/ethicsforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">⚖️</span>
            <span>EthicsForge</span>
          </NavLink>
          <NavLink to="/resilientforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🛡️</span>
            <span>ResilientForge</span>
          </NavLink>
          <NavLink to="/swarmforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🐝</span>
            <span>SwarmForge</span>
          </NavLink>
          <NavLink to="/neuroguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🧠</span>
            <span>NeuroGuard</span>
          </NavLink>
          <NavLink to="/spaceguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🛰️</span>
            <span>SpaceGuard</span>
          </NavLink>
          <NavLink to="/climateshield" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🌍</span>
            <span>ClimateShield</span>
          </NavLink>
          <NavLink to="/nanoquantum" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🔬</span>
            <span>NanoQuantum</span>
          </NavLink>
          <NavLink to="/innovateguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">💡</span>
            <span>InnovateGuard</span>
          </NavLink>
          <NavLink to="/metaforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">👁️</span>
            <span>MetaForge</span>
          </NavLink>
          <NavLink to="/droneguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🚁</span>
            <span>DroneGuard</span>
          </NavLink>
          <NavLink to="/metaguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🥽</span>
            <span>MetaGuard</span>
          </NavLink>
          <NavLink to="/finguard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🏦</span>
            <span>FinGuard</span>
          </NavLink>
          <NavLink to="/humanforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🧠</span>
            <span>HumanForge</span>
          </NavLink>
          <NavLink to="/gridshield" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">⚡</span>
            <span>GridShield</span>
          </NavLink>
          <NavLink to="/promptdefender" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🛡️</span>
            <span>PromptDefender</span>
          </NavLink>
          <NavLink to="/globaljurix" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">⚖️</span>
            <span>GlobalJurix</span>
          </NavLink>
          <NavLink to="/zerotrustforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🔐</span>
            <span>ZeroTrust</span>
          </NavLink>
          <NavLink to="/audioforensix" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🎙️</span>
            <span>AudioForensix</span>
          </NavLink>
            <NavLink to="/visualforensix" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">👁️</span>
              <span>VisualForensix</span>
            </NavLink>
            <NavLink to="/biothreatforge" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">🧬</span>
              <span>BioThreatForge</span>
            </NavLink>
          <NavLink to="/omnisimulator" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} style={{ borderLeft: '2px solid #ff0055', paddingLeft: '10px' }}>
            <span className="nav-icon" style={{ color: '#ff0055' }}>🌐</span>
            <span style={{ color: '#ff0055', fontWeight: 'bold' }}>War Room</span>
          </NavLink>
        <NavLink to="/admin" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">⚙️</span>
          <span>Admin</span>
        </NavLink>
        <NavLink to="/apthunter" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          APTHunter
        </NavLink>
        <NavLink to="/risknova" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          RiskNova
        </NavLink>
        <NavLink to="/campaignguard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          CampaignGuard
        </NavLink>
      </nav>

      <div className="header-status">
        <span className="status-dot"></span>
        ONLINE
      </div>
    </div>
  </header>
);
