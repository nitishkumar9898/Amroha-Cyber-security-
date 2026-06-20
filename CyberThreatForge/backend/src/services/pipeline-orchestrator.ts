/**
 * =============================================================================
 * PIPELINE ORCHESTRATOR — LangGraph-style Multi-Agent DAG Runtime
 * =============================================================================
 *
 * Executes investigation pipelines as directed acyclic graphs of agents.
 * Each node is a specialized agent; edges define data flow and routing.
 *
 * Architecture:
 *   PipelineOrchestrator
 *   ├── Node definitions (agent + config)
 *   ├── Edge routing (conditional + unconditional)
 *   ├── State management (shared context)
 *   └── Parallel executor (async worker pool)
 *
 * This is the LangGraph-equivalent runtime for the Node.js backend.
 * When the Python AI layer is deployed, LangGraph takes over there;
 * this runtime handles the orchestration within the Node.js API layer.
 */

import { EventEmitter } from 'node:events';
import { randomUUID } from 'node:crypto';
import { sentinelCore, InvestigationContext, Finding, InvestigationStep, Domain, Severity, Confidence } from './sentinel-core.js';
import { moduleRegistry } from './module-registry.js';

// ─── Types ──────────────────────────────────────────────────────────────────

export type NodeType = 'agent' | 'router' | 'transform' | 'sink' | 'source';
export type EdgeCondition = (state: PipelineState) => boolean;

export interface GraphNode {
  id: string;
  type: NodeType;
  agentId?: string;
  config: Record<string, unknown>;
  timeoutMs: number;
  retryCount: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  condition?: EdgeCondition;
  transform?: (data: unknown) => unknown;
}

export interface PipelineGraph {
  id: string;
  name: string;
  nodes: Map<string, GraphNode>;
  edges: GraphEdge[];
  entryNode: string;
}

export interface PipelineState {
  context: InvestigationContext;
  currentNode: string;
  nodeResults: Map<string, unknown>;
  errors: Map<string, Error>;
  startTime: number;
  metadata: Record<string, unknown>;
}

export type PipelineEvent =
  | 'pipeline:start' | 'pipeline:complete' | 'pipeline:error'
  | 'node:start' | 'node:complete' | 'node:error' | 'node:retry'
  | 'edge:traverse';

// ─── Built-in Pipeline Templates ────────────────────────────────────────────

export const STANDARD_INVESTIGATION_PIPELINE: () => PipelineGraph = () => ({
  id: 'standard-investigation',
  name: 'Standard Cyber Investigation Pipeline',
  nodes: new Map([
    ['evidence-ingestion', { id: 'evidence-ingestion', type: 'agent', config: { module: 'evidence-ingestion' }, timeoutMs: 30000, retryCount: 2 }],
    ['classification', { id: 'classification', type: 'agent', config: { module: 'classification' }, timeoutMs: 15000, retryCount: 1 }],
    ['artifact-extraction', { id: 'artifact-extraction', type: 'agent', config: { module: 'forensic-analysis' }, timeoutMs: 60000, retryCount: 2 }],
    ['vector-embedding', { id: 'vector-embedding', type: 'agent', config: { module: 'ai-embedding' }, timeoutMs: 30000, retryCount: 2 }],
    ['threat-correlation', { id: 'threat-correlation', type: 'agent', config: { module: 'threat-intel' }, timeoutMs: 45000, retryCount: 1 }],
    ['graph-correlation', { id: 'graph-correlation', type: 'agent', config: { module: 'graph-neo4j' }, timeoutMs: 30000, retryCount: 1 }],
    ['apt-attribution', { id: 'apt-attribution', type: 'agent', config: { module: 'apt-hunting' }, timeoutMs: 60000, retryCount: 1 }],
    ['ai-analysis', { id: 'ai-analysis', type: 'agent', config: { model: 'gpt-4-turbo' }, timeoutMs: 90000, retryCount: 2 }],
    ['report-generation', { id: 'report-generation', type: 'agent', config: { format: 'pdf' }, timeoutMs: 30000, retryCount: 1 }],
    ['high-confidence-early-exit', { id: 'high-confidence-early-exit', type: 'router', config: { threshold: 0.95 }, timeoutMs: 100, retryCount: 0 }],
  ]),
  edges: [
    { source: 'evidence-ingestion', target: 'classification' },
    { source: 'classification', target: 'artifact-extraction' },
    { source: 'artifact-extraction', target: 'vector-embedding' },
    { source: 'vector-embedding', target: 'threat-correlation' },
    { source: 'threat-correlation', target: 'graph-correlation' },
    // Conditional early exit if confidence is already high
    {
      source: 'graph-correlation',
      target: 'high-confidence-early-exit',
      condition: (s) => { const findings = [...s.context.findings.values()]; return findings.some(f => f.confidence >= 0.95); },
    },
    { source: 'high-confidence-early-exit', target: 'ai-analysis', condition: (s) => false }, // skip if early exit
    { source: 'graph-correlation', target: 'apt-attribution', condition: (s) => { const findings = [...s.context.findings.values()]; return findings.length > 3; } },
    { source: 'apt-attribution', target: 'ai-analysis' },
    { source: 'ai-analysis', target: 'report-generation' },
  ],
  entryNode: 'evidence-ingestion',
});

// ─── Pipeline Orchestrator ──────────────────────────────────────────────────

export class PipelineOrchestrator extends EventEmitter {
  private static instance: PipelineOrchestrator;
  private readonly pipelines = new Map<string, PipelineGraph>();
  private readonly activeRuns = new Map<string, PipelineState>();
  private readonly workerPoolSize = 4;
  private workerQueue: Array<() => Promise<void>> = [];
  private isProcessing = false;

  private constructor() {
    super();
    this.registerDefaultPipelines();
  }

  static getInstance(): PipelineOrchestrator {
    if (!PipelineOrchestrator.instance) {
      PipelineOrchestrator.instance = new PipelineOrchestrator();
    }
    return PipelineOrchestrator.instance;
  }

  private registerDefaultPipelines(): void {
    this.register(STANDARD_INVESTIGATION_PIPELINE());
  }

  register(graph: PipelineGraph): void {
    this.pipelines.set(graph.id, graph);
    this.emit('pipeline:registered', graph.id);
  }

  getPipeline(id: string): PipelineGraph | undefined {
    return this.pipelines.get(id);
  }

  async execute(pipelineId: string, context: InvestigationContext): Promise<PipelineState> {
    const graph = this.pipelines.get(pipelineId);
    if (!graph) throw new Error(`Pipeline ${pipelineId} not found`);

    const state: PipelineState = {
      context,
      currentNode: graph.entryNode,
      nodeResults: new Map(),
      errors: new Map(),
      startTime: Date.now(),
      metadata: {},
    };

    const runId = randomUUID();
    this.activeRuns.set(runId, state);
    this.emit('pipeline:start', { runId, pipelineId, contextId: context.id });

    // Topological traversal with parallel execution support
    await this.traverseGraph(graph, state, runId);

    const duration = Date.now() - state.startTime;
    this.emit('pipeline:complete', { runId, duration, nodeCount: state.nodeResults.size });
    this.activeRuns.delete(runId);

    return state;
  }

  private async traverseGraph(graph: PipelineGraph, state: PipelineState, runId: string): Promise<void> {
    const visited = new Set<string>();
    const inFlight = new Set<string>();
    const results = new Map<string, unknown>();

    const executeNode = async (nodeId: string): Promise<void> => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);
      inFlight.add(nodeId);

      const node = graph.nodes.get(nodeId);
      if (!node) throw new Error(`Node ${nodeId} not found in graph`);

      state.currentNode = nodeId;
      this.emit('node:start', { runId, nodeId });

      let lastError: Error | null = null;
      for (let attempt = 0; attempt <= node.retryCount; attempt++) {
        try {
          const result = await this.executeNodeWithTimeout(node, state);
          results.set(nodeId, result);
          state.nodeResults.set(nodeId, result);
          lastError = null;
          break;
        } catch (err) {
          lastError = err as Error;
          state.errors.set(nodeId, lastError);
          if (attempt < node.retryCount) {
            this.emit('node:retry', { runId, nodeId, attempt: attempt + 1, error: lastError.message });
          }
        }
      }

      if (lastError) {
        this.emit('node:error', { runId, nodeId, error: lastError.message });
        throw lastError;
      }

      this.emit('node:complete', { runId, nodeId, duration: Date.now() - state.startTime });
      inFlight.delete(nodeId);

      // Find next nodes via edges
      const outgoingEdges = graph.edges.filter(e => e.source === nodeId);
      const nextNodes: string[] = [];

      for (const edge of outgoingEdges) {
        const shouldTraverse = edge.condition ? edge.condition(state) : true;
        if (edge.target === 'high-confidence-early-exit' && !shouldTraverse) {
          continue; // skip early exit if condition not met
        }
        if (shouldTraverse) {
          let result = results.get(edge.source);
          if (edge.transform && result) {
            result = edge.transform(result);
          }
          nextNodes.push(edge.target);
          this.emit('edge:traverse', { runId, from: edge.source, to: edge.target });
        }
      }

      // Execute next nodes in parallel
      const uniqueNext = [...new Set(nextNodes)];
      await Promise.all(uniqueNext.map(n => executeNode(n)));
    };

    await executeNode(graph.entryNode);
  }

  private async executeNodeWithTimeout(node: GraphNode, state: PipelineState): Promise<unknown> {
    const timeout = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Node ${node.id} timed out after ${node.timeoutMs}ms`)), node.timeoutMs),
    );

    const execution = this.executeNodeHandler(node, state);
    return Promise.race([execution, timeout]);
  }

  private async executeNodeHandler(node: GraphNode, state: PipelineState): Promise<unknown> {
    switch (node.type) {
      case 'agent':
        return this.handleAgentNode(node, state);
      case 'router':
        return this.handleRouterNode(node, state);
      case 'transform':
        return node.config.transform ? (node.config.transform as Function)(state) : null;
      case 'source':
      case 'sink':
        return null;
      default:
        throw new Error(`Unknown node type: ${node.type}`);
    }
  }

  private async handleAgentNode(node: GraphNode, state: PipelineState): Promise<unknown> {
    const moduleId = node.config.module as string;
    const plugin = moduleRegistry.getPlugin(moduleId);
    if (!plugin) throw new Error(`Plugin ${moduleId} not found for agent node ${node.id}`);

    const capability = `execute_${node.id}`;
    if (typeof (plugin as any)[capability] === 'function') {
      return (plugin as any)[capability](state.context);
    }

    // Generic fallback: call the investigation hook
    if (plugin.onInvestigation) {
      return plugin.onInvestigation({
        investigationId: state.context.id,
        caseId: state.context.caseId,
        evidenceIds: state.context.evidenceIds,
        pipeline: [...state.context.pipeline],
      });
    }

    return null;
  }

  private async handleRouterNode(node: GraphNode, state: PipelineState): Promise<unknown> {
    // Router nodes evaluate conditions and set state for edge traversal
    return { routed: true, nodeId: node.id, timestamp: new Date().toISOString() };
  }

  getActiveRun(runId: string): PipelineState | undefined {
    return this.activeRuns.get(runId);
  }

  getActiveRunCount(): number {
    return this.activeRuns.size;
  }
}

export const pipelineOrchestrator = PipelineOrchestrator.getInstance();
