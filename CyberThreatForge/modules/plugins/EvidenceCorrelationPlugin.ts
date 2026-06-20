import { ModulePlugin } from '../../backend/src/services/module-registry.js';
import { ModuleManifest, InvestigationHookContext, Domain, Finding } from '../../backend/src/services/sentinel-core.js';

const CORRELATION_SVC_URL = process.env.EVIDENCE_CORRELATION_URL ?? 'http://evidence-correlation:8800';

export class EvidenceCorrelationPlugin implements ModulePlugin {
  manifest: ModuleManifest = {
    id: 'evidence-correlation-v2',
    domain: 'evidence_correlation' as Domain,
    version: '3.0.0',
    capabilities: [
      'graph-correlation', 'temporal-linking', 'multi-modal-similarity',
      'entity-correlation', 'pattern-discovery', 'anomaly-detection',
      'similarity-search', 'path-finding',
    ],
    dependencies: [],
    securityClearance: 4,
    status: 'idle',
    health: { cpu: 0, memory: 0, uptime: 0 },
  };

  async initialize(): Promise<void> {
    const resp = await fetch(`${CORRELATION_SVC_URL}/health`);
    if (!resp.ok) throw new Error(`Correlation service unavailable: ${resp.status}`);
  }

  async shutdown(): Promise<void> {}

  async healthCheck(): Promise<{ ok: boolean; details: Record<string, unknown> }> {
    try {
      const resp = await fetch(`${CORRELATION_SVC_URL}/health`);
      const body = await resp.json();
      return { ok: resp.ok, details: body };
    } catch { return { ok: false, details: { error: 'Unreachable' } }; }
  }

  async onInvestigation(context: InvestigationHookContext): Promise<Finding[]> {
    return context.evidenceIds.map(eid => ({
      id: crypto.randomUUID(), evidenceId: eid,
      type: 'evidence-correlation', severity: 'info' as const,
      description: 'Pending cross-platform evidence correlation',
      confidence: 0, timestamp: new Date().toISOString(),
      source: this.manifest.id,
      metadata: { modelVersion: 'gin-v1-bert-v1' },
    }));
  }

  async correlateGraph(evidenceIds: string[], caseId: string): Promise<any> {
    const resp = await fetch(`${CORRELATION_SVC_URL}/correlate/graph`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ evidence_ids: evidenceIds, case_id: caseId }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }

  async findSimilar(evidenceId: string, caseIds: string[]): Promise<any> {
    const resp = await fetch(`${CORRELATION_SVC_URL}/query/similar`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ evidence_id: evidenceId, case_ids: caseIds }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
  }
}
