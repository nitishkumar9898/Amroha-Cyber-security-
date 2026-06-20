export const API_BASE = '/api/responseforge';

export const createIncident = async (incidentType: string, telemetryData: any) => {
  const res = await fetch(`${API_BASE}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_type: incidentType, telemetry_data: telemetryData }),
  });
  return res.json();
};

export const generatePlaybook = async (incidentType: string, context: any) => {
  const res = await fetch(`${API_BASE}/playbooks/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_type: incidentType, context }),
  });
  return res.json();
};

export const suggestContainment = async (telemetry: any) => {
  const res = await fetch(`${API_BASE}/containment/suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(telemetry),
  });
  return res.json();
};

export const executeActions = async (actions: any[]) => {
  const res = await fetch(`${API_BASE}/actions/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(actions),
  });
  return res.json();
};
