// frontend/src/api/insider_shield.ts

import axios from "axios";

const API_BASE = "/api/insider";

export const ingestBehavior = async (payload: {
  user_id: number;
  feature_vector: number[];
  timestamp?: string;
}) => {
  const resp = await axios.post(`${API_BASE}/behavior`, payload);
  return resp.data;
};

export const ingestAccess = async (payload: {
  user_id: number;
  resource: string;
  action: string;
  outcome: string;
  timestamp?: string;
}) => {
  const resp = await axios.post(`${API_BASE}/access`, payload);
  return resp.data;
};

export const ingestExfiltration = async (payload: {
  user_id: number;
  data_size_bytes: number;
  entropy?: number;
  details?: Record<string, any>;
  timestamp?: string;
}) => {
  const resp = await axios.post(`${API_BASE}/exfiltration`, payload);
  return resp.data;
};

export const ingestPsychProfile = async (payload: {
  user_id: number;
  profile_json: Record<string, any>;
  timestamp?: string;
}) => {
  const resp = await axios.post(`${API_BASE}/psych`, payload);
  return resp.data;
};

export const fetchRiskScore = async (userId: number) => {
  const resp = await axios.get(`${API_BASE}/risk/${userId}`);
  return resp.data;
};

export const createAlert = async (payload: {
  user_id: number;
  severity: string;
  message: string;
  payload?: Record<string, any>;
}) => {
  const resp = await axios.post(`${API_BASE}/alert`, payload);
  return resp.data;
};

export const fetchAlerts = async () => {
  const resp = await axios.get(`${API_BASE}/alerts`);
  return resp.data;
};
