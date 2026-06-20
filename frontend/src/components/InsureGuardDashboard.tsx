import React, { useState, useEffect } from "react";
import axios from "axios";

export const InsureGuardDashboard: React.FC = () => {
  const [policies, setPolicies] = useState<any[]>([]);
  const [selected, setSelected] = useState<number | "">("");
  const [premiumInfo, setPremiumInfo] = useState<any>(null);

  useEffect(() => {
    axios.get("/api/insureguard/policy").then((r: any) => setPolicies(r.data));
  }, []);

  const loadPremium = (id: number) => {
    axios.get(`/api/insureguard/policy/${id}/premium-recommendation`).then((r: any) => setPremiumInfo(r.data));
  };

  return (
    <div style={{ background: "#1e1e1e", color: "#e0f7fa", minHeight: "100vh", padding: "2rem" }}>
      <h2 style={{ marginBottom: "1rem" }}>InsureGuard – Cyber Insurance Dashboard</h2>
      <div style={{ background: "#2a2a2a", padding: "1.5rem", borderRadius: "8px", marginBottom: "1rem" }}>
        <select
          value={selected}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelected(e.target.value ? Number(e.target.value) : "")}
          style={{ width: "100%", padding: "0.5rem", marginBottom: "0.5rem", background: "#333", color: "#e0f7fa", border: "1px solid #555", borderRadius: "4px" }}
        >
          <option value="" disabled>Select a policy</option>
          {policies.map((p: any) => (
            <option key={p.id} value={p.id}>#{p.policy_number} – {p.insured_entity}</option>
          ))}
        </select>
        <button
          disabled={!selected}
          onClick={() => loadPremium(selected as number)}
          style={{ padding: "0.5rem 1rem", background: "#00bcd4", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", marginTop: "0.5rem" }}
        >
          Get Premium Recommendation
        </button>
      </div>
      {premiumInfo && (
        <div style={{ background: "#2a2a2a", padding: "1.5rem", borderRadius: "8px" }}>
          <h3>Recommendation</h3>
          <p>Recommended Premium: ${premiumInfo.recommended_premium.toFixed(2)}</p>
          <pre style={{ background: "#1a1a1a", padding: "1rem", borderRadius: "4px", overflow: "auto" }}>
            {JSON.stringify(premiumInfo.risk_scores, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
