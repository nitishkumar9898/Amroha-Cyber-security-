import { ModulePlugin } from '../../backend/src/services/module-registry.js';
import { ModuleManifest, InvestigationHookContext, Domain, Finding } from '../../backend/src/services/sentinel-core.js';

const PSYCHOLOGY_SVC_URL = process.env.CYBER_PSYCHOLOGY_URL ?? 'http://cyber-psychology:8500';

export class CyberPsychologyPlugin implements ModulePlugin {
  manifest: ModuleManifest = {
    id: 'cyber-psychology-v2',
    domain: 'cyber_psychology' as Domain,
    version: '3.0.0',
    capabilities: [
      'attacker-profiling', 'insider-threat-assessment',
      'social-engineering-analysis', 'linguistic-deception-detection',
      'behavioral-timeline', 'victim-psychology',
      'escalation-prediction', 'coercion-detection',
    ],
    dependencies: ['digital-forensics'],
    securityClearance: 4,
    status: 'idle',
    health: { cpu: 0, memory: 0, uptime: 0 },
  };

  async initialize(): Promise<void> {
    const resp = await fetch(`${PSYCHOLOGY_SVC_URL}/health`);
    if (!resp.ok) throw new Error(`Psychology service unavailable: ${resp.status}`);
  }

  async shutdown(): Promise<void> {}

  async healthCheck(): Promise<{ ok: boolean; details: Record<string, unknown> }> {
    try {
      const resp = await fetch(`${PSYCHOLOGY_SVC_URL}/health`);
      const body = await resp.json();
      return { ok: resp.ok, details: body };
    } catch { return { ok: false, details: { error: 'Unreachable' } }; }
  }

  async onInvestigation(context: InvestigationHookContext): Promise<Finding[]> {
    return context.evidenceIds.map(eid => ({
      id: crypto.randomUUID(), evidenceId: eid,
      type: 'cyber-psychology', severity: 'low' as const,
      description: 'Pending behavioral profiling',
      confidence: 0, timestamp: new Date().toISOString(),
      source: this.manifest.id,
      metadata: { modelVersion: 'transformer-v1-lstm-v1' },
    }));
  }

  async profileAttacker(texts: string[], evidenceIds: string[]): Promise<any> {
    const resp = await fetch(`${PSYCHOLOGY_SVC_URL}/profile/attacker`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts, evidence_ids: evidenceIds }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async assessInsiderThreat(behavioralData: Record<string, any>): Promise<any> {
    const resp = await fetch(`${PSYCHOLOGY_SVC_URL}/profile/insider-threat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(behavioralData),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }
}
