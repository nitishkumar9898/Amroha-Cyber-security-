export const API_BASE = '/api/collabguard';

export const verifyAgencyZKP = async (agencyId: string, zkpPayload: string) => {
  const res = await fetch(`${API_BASE}/auth/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agency_id: agencyId, zkp_payload: zkpPayload }),
  });
  return res.json();
};

export const createWorkflow = async (leadAgency: string, title: string) => {
  const res = await fetch(`${API_BASE}/workflow/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lead_agency: leadAgency, title }),
  });
  return res.json();
};

export const exportComplianceSTIX = async () => {
  const res = await fetch(`${API_BASE}/compliance/export`);
  return res.json();
};
