import React, { useState } from 'react';
import { verifyAgencyZKP, createWorkflow, exportComplianceSTIX } from '../api/collabguard';
import './CollabGuardDashboard.css';

const CollabGuardDashboard: React.FC = () => {
  const [agencyId, setAgencyId] = useState('');
  const [zkpPayload, setZkpPayload] = useState('valid_zkp_mock_payload');
  const [authStatus, setAuthStatus] = useState<any>(null);
  const [invTitle, setInvTitle] = useState('');
  const [activeWorkflow, setActiveWorkflow] = useState<any>(null);
  const [stixExport, setStixExport] = useState<any>(null);

  const handleAuth = async () => {
    if (!agencyId) return;
    const res = await verifyAgencyZKP(agencyId, zkpPayload);
    setAuthStatus(res);
  };

  const handleCreateWorkflow = async () => {
    if (!agencyId || !authStatus?.access_granted) return;
    const res = await createWorkflow(agencyId, invTitle || 'Joint Operation Alpha');
    setActiveWorkflow(res);
  };

  const handleExport = async () => {
    const res = await exportComplianceSTIX();
    setStixExport(res.stix_bundle);
  };

  return (
    <div className="cg-dashboard-container">
      <div className="cg-header">
        <h1 className="cg-title">CollabGuard Secure Network</h1>
        <div className="cg-badges">
          <span className="cg-badge">ZKP Secured</span>
          <span className="cg-badge">End-to-End Encrypted</span>
        </div>
      </div>

      <div className="cg-grid">
        <div className="cg-card">
          <h2>Zero-Knowledge Authentication</h2>
          <p>Prove clearance level without revealing credentials.</p>
          <div className="cg-form">
            <input 
              type="text" 
              placeholder="Agency ID (e.g. FBI, Interpol)" 
              value={agencyId} 
              onChange={(e) => setAgencyId(e.target.value)} 
              className="cg-input"
            />
            <input 
              type="text" 
              placeholder="ZKP Payload" 
              value={zkpPayload} 
              onChange={(e) => setZkpPayload(e.target.value)} 
              className="cg-input"
            />
            <button className="cg-btn" onClick={handleAuth}>Verify Proof</button>
          </div>
          
          {authStatus && (
            <div className={`cg-auth-result ${authStatus.access_granted ? 'success' : 'failed'}`}>
              Verification: {authStatus.verification_status.toUpperCase()}
            </div>
          )}
        </div>

        <div className="cg-card">
          <h2>Joint Investigation Workspace</h2>
          <div className="cg-form">
            <input 
              type="text" 
              placeholder="Investigation Title" 
              value={invTitle} 
              onChange={(e) => setInvTitle(e.target.value)} 
              className="cg-input"
              disabled={!authStatus?.access_granted}
            />
            <button 
              className="cg-btn cg-btn-secondary" 
              onClick={handleCreateWorkflow}
              disabled={!authStatus?.access_granted}
            >
              Initialize Workspace
            </button>
          </div>
          
          {activeWorkflow && (
            <div className="cg-workflow-active">
              <p><strong>Active ID:</strong> {activeWorkflow.investigation_id}</p>
              <p>Awaiting partner agencies to join the room...</p>
            </div>
          )}
        </div>

        <div className="cg-card cg-full-width">
          <h2>Compliance & STIX Export</h2>
          <p>Export shared intelligence and audit logs in international formats.</p>
          <button className="cg-btn cg-btn-export" onClick={handleExport}>Generate STIX/TAXII Bundle</button>
          
          {stixExport && (
            <pre className="cg-pre">{JSON.stringify(JSON.parse(stixExport), null, 2)}</pre>
          )}
        </div>
      </div>
    </div>
  );
};

export default CollabGuardDashboard;
