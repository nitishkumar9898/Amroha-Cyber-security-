// frontend/src/components/SupplyChainDashboard.tsx
import React, { useEffect, useState } from "react";
import "./SupplyChainDashboard.css";
import { ingestSBOM, getRiskGraph } from "../api/supplychain";

export const SupplyChainDashboard = () => {
  const [riskGraph, setRiskGraph] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const graph = await getRiskGraph();
      setRiskGraph(graph);
      setLoading(false);
    })();
  }, []);

  const handleSBOMUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const sbomText = await file.text();
    await ingestSBOM(JSON.parse(sbomText));
    const graph = await getRiskGraph();
    setRiskGraph(graph);
  };

  return (
    <div className="supplychain-dashboard">
      <h1 className="dashboard-title">Supply Guard – Risk & Simulation</h1>
      <section className="upload-section">
        <label className="upload-label">
          📦 Upload SBOM
          <input type="file" accept=".json,.spdx,.cdx" onChange={handleSBOMUpload} />
        </label>
      </section>
      {loading && <p className="loading">Loading risk graph…</p>}
      {riskGraph && (
        <section className="graph-section">
          <pre className="graph-json">{JSON.stringify(riskGraph, null, 2)}</pre>
        </section>
      )}
    </div>
  );
};
