export const API_BASE = '/api/evolvoai';

export const submitFeedback = async (dataId: string, correctedLabel: string, analyst: string) => {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data_id: dataId, corrected_label: correctedLabel, analyst }),
  });
  return res.json();
};

export const checkDrift = async (modelId: string, recentAccuracy: number) => {
  const res = await fetch(`${API_BASE}/monitor/${modelId}?recent_accuracy=${recentAccuracy}`);
  return res.json();
};

export const triggerRetraining = async (modelId: string, datasetId: string) => {
  const res = await fetch(`${API_BASE}/train/${modelId}?dataset_id=${datasetId}`, {
    method: 'POST',
  });
  return res.json();
};

export const registerModel = async (modelId: string, version: string, metrics: any) => {
  const res = await fetch(`${API_BASE}/registry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId, version, metrics }),
  });
  return res.json();
};

export const promoteModel = async (modelId: string, version: string) => {
  const res = await fetch(`${API_BASE}/registry/${modelId}/promote/${version}`, {
    method: 'PUT',
  });
  return res.json();
};
