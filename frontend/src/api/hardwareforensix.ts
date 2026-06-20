export const API_BASE = '/api/hardwareforensix';

export const uploadFirmware = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/firmware/upload`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
};

export const analyzeTrace = async (deviceId: string, traceType: string, dataPoints: number[]) => {
  const res = await fetch(`${API_BASE}/traces/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId, trace_type: traceType, data_points: dataPoints }),
  });
  return res.json();
};

export const reverseEngineerSnippet = async (architecture: string, code: string) => {
  const res = await fetch(`${API_BASE}/firmware/re/${architecture}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });
  return res.json();
};

export const detonateFirmware = async (firmwareId: string, architecture: string = 'ARM') => {
  const res = await fetch(`${API_BASE}/firmware/sandbox/${firmwareId}?architecture=${architecture}`, {
    method: 'POST',
  });
  return res.json();
};
