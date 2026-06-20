import { ModulePlugin } from '../../backend/src/services/module-registry.js';
import { ModuleManifest, InvestigationHookContext, Domain, Finding } from '../../backend/src/services/sentinel-core.js';

const PREDICTIVE_SVC_URL = process.env.PREDICTIVE_ANALYTICS_URL ?? 'http://predictive-analytics:8700';

export class PredictiveAnalyticsPlugin implements ModulePlugin {
  manifest: ModuleManifest = {
    id: 'predictive-analytics-v2',
    domain: 'predictive_analytics' as Domain,
    version: '3.0.0',
    capabilities: [
      'threat-forecasting', 'attack-prediction', 'risk-scoring',
      'trend-analysis', 'escalation-prediction',
      'campaign-tracking', 'geopolitical-forecast',
      'seasonal-pattern-detection',
    ],
    dependencies: [],
    securityClearance: 3,
    status: 'idle',
    health: { cpu: 0, memory: 0, uptime: 0 },
  };

  async initialize(): Promise<void> {
    const resp = await fetch(`${PREDICTIVE_SVC_URL}/health`);
    if (!resp.ok) throw new Error(`Predictive service unavailable: ${resp.status}`);
  }

  async shutdown(): Promise<void> {}

  async healthCheck(): Promise<{ ok: boolean; details: Record<string, unknown> }> {
    try {
      const resp = await fetch(`${PREDICTIVE_SVC_URL}/health`);
      const body = await resp.json();
      return { ok: resp.ok, details: body };
    } catch { return { ok: false, details: { error: 'Unreachable' } }; }
  }

  async onInvestigation(context: InvestigationHookContext): Promise<Finding[]> {
    return context.evidenceIds.map(eid => ({
      id: crypto.randomUUID(), evidenceId: eid,
      type: 'predictive-analytics', severity: 'info' as const,
      description: 'Pending threat forecasting',
      confidence: 0, timestamp: new Date().toISOString(),
      source: this.manifest.id,
      metadata: { modelVersion: 'lstm-v2-prophet-v1' },
    }));
  }

  async forecastThreat(historicalData: number[], horizonDays: number): Promise<any> {
    const resp = await fetch(`${PREDICTIVE_SVC_URL}/forecast/threat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ historical_data: historicalData, horizon_days: horizonDays }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async scoreRisk(entities: Array<{ type: string; value: string }>): Promise<any> {
    const resp = await fetch(`${PREDICTIVE_SVC_URL}/score/risk`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entities }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }
}
