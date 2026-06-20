// frontend/src/api/supplychain.ts
import { API_BASE_URL } from "./config";

export const ingestSBOM = async (sbom: Record<string, any>) => {
  const resp = await fetch(`${API_BASE_URL}/supplychain/ingest_sbom`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sbom }),
  });
  return resp.json();
};

export const getRiskGraph = async () => {
  const resp = await fetch(`${API_BASE_URL}/supplychain/risk_graph`);
  return resp.json();
};

export const detectAnomaly = async (entityId: number, data: Record<string, any>) => {
  const resp = await fetch(`${API_BASE_URL}/supplychain/detect_anomaly`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity_id: entityId, data }),
  });
  return resp.json();
};

export const simulateAPT = async (name: string, parameters?: Record<string, any>) => {
  const resp = await fetch(`${API_BASE_URL}/supplychain/simulate_apt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, parameters }),
  });
  return resp.json();
};
