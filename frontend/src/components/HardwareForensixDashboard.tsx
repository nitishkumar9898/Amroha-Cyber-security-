import React, { useState } from 'react';
import { uploadFirmware, detonateFirmware } from '../api/hardwareforensix';
import './HardwareForensixDashboard.css';

const HardwareForensixDashboard: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [detonation, setDetonation] = useState<any>(null);
  const [status, setStatus] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('Uploading and analyzing firmware...');
    try {
      const res = await uploadFirmware(file);
      setAnalysis(res);
      setStatus('Analysis complete.');
    } catch (e) {
      setStatus('Upload failed.');
    }
  };

  const handleDetonate = async () => {
    setStatus('Executing in hardware sandbox...');
    // Demo ID
    const res = await detonateFirmware('fw-demo-id', 'ARM');
    setDetonation(res);
    setStatus('Sandbox execution complete.');
  };

  return (
    <div className="hf-dashboard-container">
      <h1 className="hf-title">HardwareForensix Lab</h1>

      <div className="hf-upload-zone">
        <input type="file" onChange={handleFileChange} className="hf-file-input" />
        <button className="hf-btn" onClick={handleUpload} disabled={!file}>Analyze Firmware</button>
      </div>

      {status && <div className="hf-status">{status}</div>}

      <div className="hf-grid">
        <div className="hf-card">
          <h2>Static Analysis Results</h2>
          {analysis ? (
            <div className="hf-results">
              <p><strong>SHA256:</strong> {analysis.sha256}</p>
              <p><strong>Entropy:</strong> {analysis.entropy.toFixed(2)}</p>
              <p><strong>Size:</strong> {analysis.size_bytes} bytes</p>
              <h3>Findings</h3>
              <ul>
                {analysis.analysis_results.findings?.map((f: string, i: number) => <li key={i}>{f}</li>)}
              </ul>
              <button className="hf-btn hf-btn-detonate" onClick={handleDetonate}>Detonate in Sandbox</button>
            </div>
          ) : (
            <p>Upload a firmware dump to begin.</p>
          )}
        </div>

        <div className="hf-card">
          <h2>Sandbox Telemetry</h2>
          {detonation ? (
            <pre className="hf-pre">{JSON.stringify(detonation, null, 2)}</pre>
          ) : (
            <p>Awaiting detonation...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default HardwareForensixDashboard;
