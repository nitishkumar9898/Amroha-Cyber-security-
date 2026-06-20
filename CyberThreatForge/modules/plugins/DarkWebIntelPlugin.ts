import { ModulePlugin } from '../../backend/src/services/module-registry.js';
import { ModuleManifest, InvestigationHookContext, Domain, Finding } from '../../backend/src/services/sentinel-core.js';

const DARKWEB_SVC_URL = process.env.DARKWEB_INTEL_URL ?? 'http://darkweb-intel:8400';

export class DarkWebIntelPluginV2 implements ModulePlugin {
  manifest: ModuleManifest = {
    id: 'darkweb-intel-v2',
    domain: 'darkweb' as Domain,
    version: '3.0.0',
    capabilities: [
      'tor-crawling', 'i2p-monitoring', 'breach-monitoring',
      'marketplace-scraping', 'actor-profiling', 'ransomware-tracking',
      'threat-classification', 'darkweb-pii-detection',
    ],
    dependencies: [],
    securityClearance: 5,
    status: 'idle',
    health: { cpu: 0, memory: 0, uptime: 0 },
  };

  async initialize(): Promise<void> {
    const resp = await fetch(`${DARKWEB_SVC_URL}/health`);
    if (!resp.ok) throw new Error(`DarkWeb service unavailable: ${resp.status}`);
  }

  async shutdown(): Promise<void> {}

  async healthCheck(): Promise<{ ok: boolean; details: Record<string, unknown> }> {
    try {
      const resp = await fetch(`${DARKWEB_SVC_URL}/health`);
      const body = await resp.json();
      return { ok: resp.ok, details: body };
    } catch { return { ok: false, details: { error: 'Unreachable' } }; }
  }

  async onInvestigation(context: InvestigationHookContext): Promise<Finding[]> {
    return context.evidenceIds.map(eid => ({
      id: crypto.randomUUID(), evidenceId: eid,
      type: 'darkweb-intel', severity: 'medium' as const,
      description: 'Pending dark web intelligence gathering',
      confidence: 0, timestamp: new Date().toISOString(),
      source: this.manifest.id,
      metadata: { modelVersion: '3.0.0' },
    }));
  }

  async crawlTor(url: string): Promise<any> {
    const resp = await fetch(`${DARKWEB_SVC_URL}/crawl/tor`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async monitorBreaches(email: string): Promise<any> {
    const resp = await fetch(`${DARKWEB_SVC_URL}/monitor/breaches`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async profileActor(username: string, platform: string): Promise<any> {
    const resp = await fetch(`${DARKWEB_SVC_URL}/analyze/actor`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, platform }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }
}
