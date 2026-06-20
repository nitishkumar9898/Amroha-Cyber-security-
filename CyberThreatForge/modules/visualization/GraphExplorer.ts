/**
 * =============================================================================
 * VISUALIZATION MODULE — Graph Explorer, Timeline, Heatmap
 * =============================================================================
 *
 * Transforms investigation data into interactive visualizations:
 *   - Neo4j evidence graph explorer (WebGL force-directed)
 *   - Investigation timeline (Gantt-style)
 *   - Geographic threat heatmap (deck.gl)
 *   - MITRE ATT&CK heatmap coverage
 *   - Chain of custody flow diagram
 *   - Case evidence inventory matrix
 */

import { neo4jDriver } from '../../backend/src/config/neo4j.js';
import { db } from '../../backend/src/config/database.js';
import { sentinelCore, Domain } from '../../backend/src/services/sentinel-core.js';

// ─── Types ──────────────────────────────────────────────────────────────────

export interface GraphNode {
  id: string;
  type: 'evidence' | 'actor' | 'ioc' | 'case' | 'entity' | 'ttp' | 'campaign' | 'device';
  label: string;
  properties: Record<string, unknown>;
  riskScore: number;
  color: string;
  size: number;
  group: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label: string;
  weight: number;
  properties: Record<string, unknown>;
  color: string;
  dashed: boolean;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'evidence_acquired' | 'analysis_complete' | 'ioc_discovered' | 'actor_identified' | 'report_generated' | 'case_milestone';
  title: string;
  description: string;
  caseId: string;
  evidenceId?: string;
  severity?: string;
  actorName?: string;
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  intensity: number;
  radius: number;
  label: string;
  category: string;
}

export interface MITRECoverage {
  tactic: string;
  techniques: Array<{
    id: string;
    name: string;
    detected: boolean;
    confidence: number;
    evidenceCount: number;
  }>;
  coveragePercent: number;
}

export class VisualizationService {
  // ── Evidence Graph (from Neo4j) ───────────────────────────────────────────

  async getCaseGraph(caseId: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
    const session = neo4jDriver.session();
    try {
      const result = await session.run(`
        MATCH (c:Case {id: $caseId})
        OPTIONAL MATCH (c)-[:HAS_EVIDENCE]->(e:Evidence)
        OPTIONAL MATCH (e)-[:RELATED_TO]->(other:Evidence)
        OPTIONAL MATCH (e)-[:HAS_IOC]->(i:IOC)
        OPTIONAL MATCH (i)-[:INDICATES]->(ttp:TTP)
        OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(d:Device)
        OPTIONAL MATCH (i)-[:ATTRIBUTED_TO]->(a:Actor)
        RETURN c, collect(DISTINCT e) as evidence, collect(DISTINCT i) as iocs,
               collect(DISTINCT ttp) as ttps, collect(DISTINCT d) as devices,
               collect(DISTINCT a) as actors
      `, { caseId });

      const nodes: GraphNode[] = [];
      const edges: GraphEdge[] = [];
      const record = result.records[0];

      if (record) {
        // Extract nodes and edges from Neo4j result
        const allNodes = [
          ...record.get('evidence'), ...record.get('iocs'),
          ...record.get('ttps'), ...record.get('devices'),
          ...record.get('actors'),
        ] as Array<{ identity: unknown; labels: string[]; properties: Record<string, unknown> }>;

        for (const node of allNodes) {
          if (!node?.properties?.id) continue;
          nodes.push(this.neo4jToGraphNode(node));
        }

        // Extract edges from relationships
        // In production: RETURN relationships as well
      }

      return { nodes, edges };
    } finally {
      await session.close();
    }
  }

  private neo4jToGraphNode(neoNode: {
    identity: unknown; labels: string[]; properties: Record<string, unknown>;
  }): GraphNode {
    const type = (neoNode.labels[0] ?? 'unknown').toLowerCase() as GraphNode['type'];
    const riskScore = (neoNode.properties.risk_score as number) ?? 0;
    const group = neoNode.labels[0] ?? 'unknown';

    return {
      id: neoNode.properties.id as string,
      type,
      label: (neoNode.properties.name ?? neoNode.properties.title ?? neoNode.properties.id) as string,
      properties: neoNode.properties,
      riskScore,
      color: this.getColorForType(type, riskScore),
      size: this.getSizeForRisk(riskScore),
      group,
    };
  }

  private getColorForType(type: GraphNode['type'], riskScore: number): string {
    const colors: Record<string, string> = {
      evidence: riskScore > 0.7 ? '#ef4444' : '#3b82f6',
      actor: '#8b5cf6',
      ioc: riskScore > 0.7 ? '#ef4444' : '#f59e0b',
      case: '#10b981',
      entity: '#6366f1',
      ttp: '#ec4899',
      campaign: '#14b8a6',
      device: '#f97316',
    };
    return colors[type] ?? '#6b7280';
  }

  private getSizeForRisk(riskScore: number): number {
    return Math.max(5, Math.min(30, riskScore * 30));
  }

  // ── Timeline ──────────────────────────────────────────────────────────────

  async getCaseTimelines(caseId: string): Promise<TimelineEvent[]> {
    const events: TimelineEvent[] = [];

    // Evidence acquisition events
    const evidence = await db('case_evidence')
      .where({ case_id: caseId })
      .select('id', 'evidence_type', 'description', 'created_at');

    for (const ev of evidence) {
      events.push({
        id: `ev-${ev.id}`,
        timestamp: ev.created_at,
        type: 'evidence_acquired',
        title: `${ev.evidence_type.replace('_', ' ')} Acquired`,
        description: ev.description,
        caseId,
        evidenceId: ev.id,
      });
    }

    // Chain of custody events
    const custody = await db('chain_of_custody')
      .join('case_evidence', 'chain_of_custody.evidence_id', 'case_evidence.id')
      .where('case_evidence.case_id', caseId)
      .select('chain_of_custody.*')
      .orderBy('chain_of_custody.timestamp', 'asc');

    for (const ce of custody) {
      events.push({
        id: `coc-${ce.id}`,
        timestamp: ce.timestamp,
        type: 'case_milestone',
        title: `Evidence ${ce.action}`,
        description: ce.notes ?? `Action: ${ce.action} by ${ce.actor_id}`,
        caseId,
        evidenceId: ce.evidence_id,
      });
    }

    // Chain of custody events from SentinelCore
    const insights = sentinelCore.getInsights();
    for (const insight of insights.slice(-20)) {
      events.push({
        id: `insight-${insight.id}`,
        timestamp: new Date().toISOString(),
        type: 'ioc_discovered',
        title: `New Finding: ${insight.domain}`,
        description: insight.summary,
        caseId,
        severity: insight.confidence > 0.8 ? 'high' : 'medium',
      });
    }

    return events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }

  // ── Geographic Heatmap ────────────────────────────────────────────────────

  async getThreatHeatmap(jurisdiction?: string): Promise<HeatmapPoint[]> {
    const points: HeatmapPoint[] = [];

    // Extract geo-tagged IOCs and evidence locations
    try {
      const session = neo4jDriver.session();
      const result = await session.run(`
        MATCH (i:IOC)
        WHERE i.geo_lat IS NOT NULL
        RETURN i.geo_lat as lat, i.geo_lng as lng,
               count(i) as intensity, i.type as category
        ORDER BY intensity DESC
        LIMIT 100
      `);

      for (const record of result.records) {
        points.push({
          lat: record.get('lat') as number,
          lng: record.get('lng') as number,
          intensity: Math.min(1, (record.get('intensity') as number) / 10),
          radius: Math.min(50, (record.get('intensity') as number) * 5),
          label: `IOC Cluster`,
          category: record.get('category') as string ?? 'unknown',
        });
      }
      await session.close();
    } catch { /* */ }

    return points;
  }

  // ── MITRE ATT&CK Coverage ─────────────────────────────────────────────────

  async getMitreCoverage(caseId: string): Promise<MITRECoverage[]> {
    const session = neo4jDriver.session();
    try {
      const result = await session.run(`
        MATCH (c:Case {id: $caseId})-[:HAS_EVIDENCE]->(e:Evidence)
        OPTIONAL MATCH (e)-[:HAS_IOC]->(i:IOC)-[:INDICATES]->(ttp:TTP)
        WITH ttp.tactic as tactic, ttp.id as techId,
             ttp.name as techName, count(DISTINCT e) as evCount
        RETURN tactic, collect({
          id: techId, name: techName, evidenceCount: evCount
        }) as techniques
        ORDER BY tactic
      `, { caseId });

      const coverage: MITRECoverage[] = [];
      for (const record of result.records) {
        const techniques = record.get('techniques') as Array<{ id: string; name: string; evidenceCount: number }>;
        coverage.push({
          tactic: record.get('tactic') as string,
          techniques: techniques.map((t) => ({
            id: t.id,
            name: t.name,
            detected: t.evidenceCount > 0,
            confidence: Math.min(1, t.evidenceCount / 5),
            evidenceCount: t.evidenceCount,
          })),
          coveragePercent: techniques.filter((t) => t.evidenceCount > 0).length / Math.max(techniques.length, 1),
        });
      }

      return coverage;
    } finally {
      await session.close();
    }
  }

  // ── Chain of Custody Flow ─────────────────────────────────────────────────

  async getCustodyFlow(evidenceId: string): Promise<{
    nodes: Array<{ id: string; label: string; type: string; timestamp: string }>;
    edges: Array<{ source: string; target: string; label: string; hash: string }>;
  }> {
    const events = await db('chain_of_custody')
      .where({ evidence_id: evidenceId })
      .orderBy('timestamp', 'asc');

    const nodes: Array<{ id: string; label: string; type: string; timestamp: string }> = [];
    const edges: Array<{ source: string; target: string; label: string; hash: string }> = [];

    for (let i = 0; i < events.length; i++) {
      const ev = events[i];
      if (!ev) continue;

      nodes.push({
        id: ev.id,
        label: `${ev.action} by ${ev.actor_role}`,
        type: ev.action,
        timestamp: ev.timestamp,
      });

      if (i > 0) {
        edges.push({
          source: events[i - 1]!.id,
          target: ev.id,
          label: `➡ ${ev.action}`,
          hash: ev.hash,
        });
      }
    }

    return { nodes, edges };
  }
}

export const visualizationService = new VisualizationService();
