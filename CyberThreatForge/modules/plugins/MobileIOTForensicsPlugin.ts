import { ModulePlugin } from '../../backend/src/services/module-registry.js';
import { ModuleManifest, InvestigationHookContext, Domain, Finding } from '../../backend/src/services/sentinel-core.js';

const MOBILE_SVC_URL = process.env.MOBILE_IOT_URL ?? 'http://mobile-iot-forensics:8300';

export class MobileIOTForensicsPlugin implements ModulePlugin {
  manifest: ModuleManifest = {
    id: 'mobile-iot-forensics-v2',
    domain: 'mobile_forensics' as Domain,
    version: '3.0.0',
    capabilities: [
      'android-forensics', 'ios-forensics', 'iot-forensics',
      'timeline-analysis', 'communication-analysis',
      'location-intelligence', 'app-usage-analysis',
    ],
    dependencies: ['evidence-ingestion'],
    securityClearance: 3,
    status: 'idle',
    health: { cpu: 0, memory: 0, uptime: 0 },
  };

  async initialize(): Promise<void> {
    const resp = await fetch(`${MOBILE_SVC_URL}/health`);
    if (!resp.ok) throw new Error(`Mobile/IoT service unavailable: ${resp.status}`);
  }

  async shutdown(): Promise<void> {}

  async healthCheck(): Promise<{ ok: boolean; details: Record<string, unknown> }> {
    try {
      const resp = await fetch(`${MOBILE_SVC_URL}/health`);
      const body = await resp.json();
      return { ok: resp.ok, details: body };
    } catch { return { ok: false, details: { error: 'Unreachable' } }; }
  }

  async onInvestigation(context: InvestigationHookContext): Promise<Finding[]> {
    return context.evidenceIds.map(eid => ({
      id: crypto.randomUUID(), evidenceId: eid,
      type: 'mobile-iot-forensics', severity: 'medium' as const,
      description: 'Pending mobile/IoT forensic analysis',
      confidence: 0, timestamp: new Date().toISOString(),
      source: this.manifest.id,
      metadata: { modelVersion: '3.0.0' },
    }));
  }

  async extractAndroid(dumpPath: string): Promise<any> {
    const resp = await fetch(`${MOBILE_SVC_URL}/extract/android`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dump_path: dumpPath }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async extractIOS(backupPath: string): Promise<any> {
    const resp = await fetch(`${MOBILE_SVC_URL}/extract/ios`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ backup_path: backupPath }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }
}
