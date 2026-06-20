export interface AnalysisResult {
  sequence_id: string;
  bioweapon_probability: number;
  source_facility: string;
  timestamp: string;
}

export async function fetchAnalysis(): Promise<AnalysisResult[]> {
  const response = await fetch('/api/biothreatforge/analysis', {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch analysis data: ${response.statusText}`);
  }
  const data: AnalysisResult[] = await response.json();
  return data;
}
