// src/api/training.ts
import axios from 'axios';

// Base URL – will be set via VITE_BACKEND_URL env var
const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/**
 * Start a new training session.
 */
export const startTraining = async (payload: {
  user_id: string;
  scenario_name: string;
  config?: Record<string, any>;
}) => {
  const response = await axios.post(`${API_BASE}/api/training/start`, payload, {
    withCredentials: true,
  });
  return response.data;
};

/**
 * Submit a training result metric.
 */
export const submitResult = async (payload: {
  session_id: number;
  metric_name: string;
  metric_value: number;
  details?: Record<string, any>;
}) => {
  const response = await axios.post(`${API_BASE}/api/training/submit`, payload, {
    withCredentials: true,
  });
  return response.data;
};

/**
 * Retrieve scenario hints for a training session.
 */
export const getHints = async (session_id: number) => {
  const response = await axios.get(`${API_BASE}/api/training/hints/${session_id}`, {
    withCredentials: true,
  });
  return response.data;
};

/**
 * Retrieve all results for a training session.
 */
export const getResults = async (session_id: number) => {
  const response = await axios.get(`${API_BASE}/api/training/results/${session_id}`, {
    withCredentials: true,
  });
  return response.data;
};
