export const About = () => (
  <section className="animate-in about-section">
    <div className="dashboard-header">
      <h1 className="section-title">
        <span className="icon">🛡️</span>
        <span className="text-gradient">CyberThreatForge Platform</span>
      </h1>
      <p className="section-subtitle">Advanced Persistent Threat simulation range and Section 63 BSA compliance audit pipeline.</p>
    </div>

    <div className="panel" style={{ marginBottom: '24px' }}>
      <h3>Platform Architecture</h3>
      <p style={{ marginTop: '8px', fontSize: '0.9rem' }}>
        CyberThreatForge is a state-of-the-art cyber-security threat simulation range designed to assist law enforcement agencies (LEAs), compliance teams, and forensic analysts in recreating modern multi-channel attacks. The platform couples realistic cyber-attack vectors with automated digital chain-of-custody logging to satisfy modern legal admissibility requirements in court.
      </p>
    </div>

    <h3 style={{ marginBottom: '16px' }}>Forensic Toolsets & Decoders</h3>
    <div className="about-features">
      
      <div className="about-feature">
        <div className="feature-icon">📹</div>
        <h4>Deepfake Detection</h4>
        <p>Analyze media payloads (video/audio) using forensic markers to calculate neural manipulation scores and locate spatial irregularities.</p>
      </div>

      <div className="about-feature">
        <div className="feature-icon">☣️</div>
        <h4>Malware Sandbox</h4>
        <p>Deploy binary executables in an isolated host sandbox. Intercept network endpoints, API hooks, and analyze registry manipulation.</p>
      </div>

      <div className="about-feature">
        <div className="feature-icon">📱</div>
        <h4>Mobile Device Parser</h4>
        <p>Extract SQLite records from messaging databases, resolve coordinate metadata, and reconstruct contact exchange logs.</p>
      </div>

      <div className="about-feature">
        <div className="feature-icon">🧅</div>
        <h4>Dark Web Intelligence</h4>
        <p>Scrape Tor network directory endpoints to search for leaks, credential dumps, and actor bitcoin transaction wallets.</p>
      </div>

      <div className="about-feature">
        <div className="feature-icon">🔌</div>
        <h4>Hardware Audit compliance</h4>
        <p>Inspect connected USB peripherals against regulatory tables (Vendor ID, Product ID, and serial signatures) to flag BadUSB/Ducky payloads.</p>
      </div>

      <div className="about-feature">
        <div className="feature-icon">🧠</div>
        <h4>Cyber Psychology</h4>
        <p>Apply natural language processing to ransom messages or social engineering lures to determine threat urgency and psychological profiling indices.</p>
      </div>

    </div>

    <div className="panel" style={{ marginTop: '24px', background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.05), rgba(139, 92, 246, 0.08))', border: '1px solid var(--border-accent)' }}>
      <h3>Legal Framework & Compliance Compliance</h3>
      <p style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
        Under the new Indian penal statutes, digital evidence admissibility standards have been modernized. CyberThreatForge features automated reporting workflows that target the following specific compliance markers:
      </p>
      <ul style={{ paddingLeft: '20px', marginTop: '12px', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <li>
          <strong>Section 63 Bharatiya Sakshya Adhiniyam (BSA), 2023:</strong> Replaces Section 65B of the Indian Evidence Act, mandating secure digital hashes (SHA-256) and examiner designations to certify the integrity of computer outputs.
        </li>
        <li>
          <strong>Digital Personal Data Protection (DPDP) Act, 2023:</strong> Restricts PII leaks and mandates timely 6-hour incident reports to the Indian Computer Emergency Response Team (CERT-IN).
        </li>
        <li>
          <strong>Information Technology Act, 2000 (Section 66):</strong> Targets unauthorized network intrusion, computer source manipulation, and cyber terrorism.
        </li>
      </ul>
    </div>
  </section>
);
export default About;
