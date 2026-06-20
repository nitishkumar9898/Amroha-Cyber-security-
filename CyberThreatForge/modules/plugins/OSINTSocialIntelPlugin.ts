import { ModulePlugin } from '../../backend/src/services/module-registry.js';
import { ModuleManifest, InvestigationHookContext, Domain, Finding } from '../../backend/src/services/sentinel-core.js';

const OSINT_SVC_URL = process.env.OSINT_SOCIAL_URL ?? 'http://osint-social-intel:8600';

export class OSINTSocialIntelPlugin implements ModulePlugin {
  manifest: ModuleManifest = {
    id: 'osint-social-intel-v2',
    domain: 'osint' as Domain,
    version: '3.0.0',
    capabilities: [
      'social-media-collection', 'domain-intelligence',
      'ip-intelligence', 'email-osint',
      'entity-resolution', 'sentiment-tracking',
      'social-network-analysis', 'digital-footprint',
    ],
    dependencies: [],
    securityClearance: 2,
    status: 'idle',
    health: { cpu: 0, memory: 0, uptime: 0 },
  };

  async initialize(): Promise<void> {
    const resp = await fetch(`${OSINT_SVC_URL}/health`);
    if (!resp.ok) throw new Error(`OSINT service unavailable: ${resp.status}`);
  }

  async shutdown(): Promise<void> {}

  async healthCheck(): Promise<{ ok: boolean; details: Record<string, unknown> }> {
    try {
      const resp = await fetch(`${OSINT_SVC_URL}/health`);
      const body = await resp.json();
      return { ok: resp.ok, details: body };
    } catch { return { ok: false, details: { error: 'Unreachable' } }; }
  }

  async onInvestigation(context: InvestigationHookContext): Promise<Finding[]> {
    return context.evidenceIds.map(eid => ({
      id: crypto.randomUUID(), evidenceId: eid,
      type: 'osint', severity: 'info' as const,
      description: 'Pending OSINT collection',
      confidence: 0, timestamp: new Date().toISOString(),
      source: this.manifest.id,
      metadata: { modelVersion: '3.0.0' },
    }));
  }

  async collectDomain(domain: string): Promise<any> {
    const resp = await fetch(`${OSINT_SVC_URL}/collect/domain`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async resolveEntity(name: string, platform?: string): Promise<any> {
    const resp = await fetch(`${OSINT_SVC_URL}/analyze/entity`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, platform }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }
}
