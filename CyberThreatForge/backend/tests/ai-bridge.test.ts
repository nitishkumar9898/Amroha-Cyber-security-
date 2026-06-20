import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sentinelAIBridge } from '../src/services/sentinel-ai-bridge.js';

// ─── Mocks ───────────────────────────────────────────────────────────────────

vi.mock('../src/middleware/auth.js', () => ({
  requireRole: (..._roles: string[]) => {
    return async (_req: any, _reply: any) => {};
  },
}));

vi.mock('../../ai-layer/sentinel-ai-core.js', () => ({
  sentinelAI: {
    analyze: vi.fn(),
    findModels: vi.fn(),
    findAgents: vi.fn(),
    getMetrics: vi.fn(),
    registerModel: vi.fn(),
    capabilities: ['text', 'image', 'binary', 'audio', 'video', 'network', 'code'],
  },
  AIResponse: class {},
  Modality: { TEXT: 'text' },
}));

vi.mock('../../ai-layer/continual-learning-engine.js', () => ({
  continualLearning: {
    ingestTrainingExample: vi.fn(),
    ingestHumanFeedback: vi.fn(),
    triggerLearning: vi.fn(),
    getMetrics: vi.fn(),
    getLatestSnapshot: vi.fn(),
  },
  LearningTrigger: { FEEDBACK: 'feedback', MANUAL: 'manual', SCHEDULED: 'scheduled' },
}));

vi.mock('../../ai-layer/models/ensemble-manager.js', () => ({
  ensembleManager: {
    predict: vi.fn(),
    getOverallAccuracy: vi.fn(),
    ensembles: new Map(),
  },
}));

vi.mock('../../ai-layer/explainability/xai-provider.js', () => ({
  xaiProvider: {
    explain: vi.fn(),
    generateEthicsReport: vi.fn(),
  },
  ExplanationLevel: { SHALLOW: 'shallow', STANDARD: 'standard', DEEP: 'deep', FORENSIC: 'forensic' },
}));

vi.mock('../services/sentinel-core.js', () => ({
  sentinelCore: { getSystemHealth: vi.fn() },
}));

// ─── Helpers ─────────────────────────────────────────────────────────────────

function createMockFastify() {
  const routes = new Map<string, { method: string; path: string; handler: Function; preHandler?: Function[] }>();

  function register(method: string, path: string, opts: any, handler?: Function) {
    if (typeof opts === 'function') { handler = opts; opts = {}; }
    const wrapped = async (req: any, reply: any) => {
      try {
        const result = await handler!(req, reply);
        if (result !== undefined && !reply._sent) {
          reply._sent = true;
          reply._body = result;
        }
      } catch (err) {
        reply._error = err;
        reply._sent = true;
        reply._body = { error: err instanceof Error ? err.message : String(err) };
      }
      return reply;
    };
    routes.set(`${method} ${path}`, { method, path, handler: wrapped, preHandler: opts?.preHandler });
  }

  return {
    post: vi.fn((p: string, o: any, h?: Function) => register('POST', p, o, h)),
    get: vi.fn((p: string, o: any, h?: Function) => register('GET', p, o, h)),
    _routes: routes,
    _getRoute: (method: string, path: string) => routes.get(`${method} ${path}`),
  };
}

function mockRequest(overrides: any = {}): any {
  return {
    body: overrides.body ?? {},
    query: overrides.query ?? {},
    params: overrides.params ?? {},
    user: overrides.user ?? { sub: 'tester', role: 'admin' },
    jwtVerify: vi.fn(),
    ...overrides,
  };
}

function mockReply(): any {
  const r: any = {
    _status: 200, _body: null, _sent: false, _error: null,
    status: vi.fn(function (c: number) { r._status = c; return r; }),
    send: vi.fn(function (b: any) { r._body = b; r._sent = true; return r; }),
  };
  return r;
}

async function invoke(app: any, method: string, path: string, body?: any) {
  const route = app._getRoute(method, path);
  if (!route) throw new Error(`Route ${method} ${path} not found`);
  const req = mockRequest(body ? { body } : {});
  const reply = mockReply();
  const result = await route.handler(req, reply);
  return { status: reply._status, body: reply._body, error: reply._error, reply: result };
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('sentinelAIBridge', () => {
  let app: any;

  beforeEach(async () => {
    vi.clearAllMocks();
    app = createMockFastify();
    await sentinelAIBridge(app);
  });

  describe('Route Registration', () => {
    it('registers all endpoints', async () => {
      await sentinelAIBridge(app);
      expect(app._routes.size).toBe(11);
    });

    it.each([
      ['POST', '/ai/analyze'],
      ['POST', '/ai/explain'],
      ['POST', '/ai/feedback'],
      ['POST', '/ai/ensemble/predict'],
      ['GET', '/ai/ensemble/list'],
      ['GET', '/ai/agents'],
      ['GET', '/ai/models'],
      ['GET', '/ai/learning/metrics'],
      ['POST', '/ai/learning/trigger'],
      ['POST', '/ai/ethics/report'],
      ['POST', '/ai/models/register'],
    ])('registers %s %s', async (method, path) => {
      await sentinelAIBridge(app);
      const route = app._getRoute(method, path);
      expect(route).toBeDefined();
      expect(route.preHandler).toBeDefined();
    });
  });

  describe('POST /ai/analyze', () => {
    it('analyzes text input and returns response', async () => {
      const { sentinelAI } = await import('../../ai-layer/sentinel-ai-core.js');
      vi.mocked(sentinelAI.analyze).mockResolvedValue({
        id: 'ana-1', requestId: 'req-1',
        outputs: [{ type: 'classification', modelName: 'cnn', modelVersion: '1', output: { class: 'malicious' }, confidence: 0.92 }],
        fusionResult: null, confidence: 0.92,
        uncertainty: { overall: 0.08, sources: [] },
        processingTimeMs: 342, modelChain: ['cnn'],
        ethicsCheck: { passed: true, humanReviewRequired: false, checks: [], recommendations: [] },
        timestamp: '2026-01-01T00:00:00Z', metadata: {},
      });

      const res = await invoke(app, 'POST', '/ai/analyze', {
        input: 'Suspicious process', context: { domain: 'malware_analysis', requireXAI: true },
      });
      expect(res.body.id).toBe('ana-1');
      expect(res.body.confidence).toBe(0.92);
    });

    it('rejects input with missing context', async () => {
      const res = await invoke(app, 'POST', '/ai/analyze', { input: 'test' });
      expect(res.body.error).toMatch(/required/i);
    });
  });

  describe('POST /ai/explain', () => {
    it('generates XAI explanation', async () => {
      const { xaiProvider } = await import('../../ai-layer/explainability/xai-provider.js');
      vi.mocked(xaiProvider.explain).mockResolvedValue({
        id: 'xai-1', summary: 'File classified as malicious', keyFindings: [],
        confidenceStatement: 'High', limitations: [], disclaimer: 'Test',
      });

      const res = await invoke(app, 'POST', '/ai/explain', {
        analysisId: '00000000-0000-0000-0000-000000000001',
        level: 'standard', audience: 'investigator', language: 'en',
      });
      expect(res.body.summary).toContain('malicious');
    });
  });

  describe('POST /ai/feedback', () => {
    it('records positive feedback', async () => {
      const { continualLearning } = await import('../../ai-layer/continual-learning-engine.js');

      const res = await invoke(app, 'POST', '/ai/feedback', {
        analysisId: '00000000-0000-0000-0000-000000000001', rating: 1, comments: 'Good',
      });
      expect(res.body.ok).toBe(true);
      expect(continualLearning.ingestHumanFeedback).toHaveBeenCalledOnce();
    });

    it('triggers learning on negative feedback', async () => {
      vi.useFakeTimers();
      const { continualLearning } = await import('../../ai-layer/continual-learning-engine.js');

      await invoke(app, 'POST', '/ai/feedback', {
        analysisId: '00000000-0000-0000-0000-000000000001', rating: -1, correction: { correct_class: 'benign' },
      });
      vi.advanceTimersToNextTimer();
      expect(continualLearning.triggerLearning).toHaveBeenCalledWith('feedback');
      vi.useRealTimers();
    });

    it('rejects invalid rating', async () => {
      const res = await invoke(app, 'POST', '/ai/feedback', {
        analysisId: '00000000-0000-0000-0000-000000000001', rating: 5,
      });
      expect(res.body.error).toMatch(/rating/i);
    });
  });

  describe('POST /ai/ensemble/predict', () => {
    it('runs ensemble prediction', async () => {
      const { ensembleManager } = await import('../../ai-layer/models/ensemble-manager.js');
      vi.mocked(ensembleManager.predict).mockResolvedValue({
        ensembleId: 'malware-classification-ensemble', finalPrediction: 'malicious',
        confidence: 0.94, agreementScore: 0.87, uncertaintyLevel: 'low',
        individualPredictions: [], method: 'weighted_average',
      });

      const res = await invoke(app, 'POST', '/ai/ensemble/predict', {
        ensembleId: 'malware-classification-ensemble',
        modelOutputs: [{ modelId: 'cnn', output: 'malicious', confidence: 0.92 }],
      });
      expect(res.body.agreementScore).toBe(0.87);
    });
  });

  describe('GET /ai/agents', () => {
    it('returns registered agents', async () => {
      const { sentinelAI } = await import('../../ai-layer/sentinel-ai-core.js');
      vi.mocked(sentinelAI.findAgents).mockReturnValue([
        { id: 'agent-1', name: 'Agent 1', description: 'Test', domain: 'test', modelIds: [], inputModalities: ['text'], outputModalities: ['text'], capabilities: ['analysis'], status: 'active' },
      ]);

      const res = await invoke(app, 'GET', '/ai/agents');
      expect(res.body.agents).toHaveLength(1);
      expect(res.body.agents[0].id).toBe('agent-1');
    });
  });

  describe('GET /ai/models', () => {
    it('returns registered models', async () => {
      const { sentinelAI } = await import('../../ai-layer/sentinel-ai-core.js');
      vi.mocked(sentinelAI.findModels).mockReturnValue([
        { id: 'm1', name: 'M1', version: '1', modalities: ['text'], capabilities: ['analysis'], accuracy: 0.9, latencyMs: 100, maxInputSize: 1000, requiresGpu: false, modelType: 'classifier', status: 'active' },
      ]);

      const res = await invoke(app, 'GET', '/ai/models');
      expect(res.body.models).toHaveLength(1);
    });
  });

  describe('GET /ai/ensemble/list', () => {
    it('returns all ensembles', async () => {
      const res = await invoke(app, 'GET', '/ai/ensemble/list');
      expect(res.body.ensembles).toHaveLength(5);
      expect(res.body.ensembles[0].id).toBe('malware-classification-ensemble');
    });
  });

  describe('GET /ai/learning/metrics', () => {
    it('returns learning metrics', async () => {
      const { sentinelAI } = await import('../../ai-layer/sentinel-ai-core.js');
      const { continualLearning } = await import('../../ai-layer/continual-learning-engine.js');
      const { ensembleManager } = await import('../../ai-layer/models/ensemble-manager.js');

      vi.mocked(sentinelAI.getMetrics).mockReturnValue({ totalRequests: 100, avgLatencyMs: 250, modelCount: 8, agentCount: 8 });
      vi.mocked(continualLearning.getMetrics).mockReturnValue({ replayBufferSize: 500, activeAdapters: 3, avgAccuracy: 0.85, totalExamples: 500, scheduledTrainingInterval: 3600000, lastTrainingRun: '2026-01-01T00:00:00Z', totalFeedbackProcessed: 50 });
      vi.mocked(continualLearning.getLatestSnapshot).mockReturnValue({ id: 'snap-1', timestamp: '2026-01-01T00:00:00Z', accuracy: 0.85, models: 8 });
      vi.mocked(ensembleManager.getOverallAccuracy).mockReturnValue(0.89);

      const res = await invoke(app, 'GET', '/ai/learning/metrics');
      expect(res.body.continualLearning.replayBufferSize).toBe(500);
      expect(res.body.ensembleAccuracy).toBe(0.89);
    });
  });

  describe('POST /ai/learning/trigger', () => {
    it('triggers manual learning cycle', async () => {
      const { continualLearning } = await import('../../ai-layer/continual-learning-engine.js');

      const res = await invoke(app, 'POST', '/ai/learning/trigger', { trigger: 'manual' });
      expect(res.body.ok).toBe(true);
      expect(continualLearning.triggerLearning).toHaveBeenCalledWith('manual');
    });
  });

  describe('POST /ai/ethics/report', () => {
    it('generates ethics report', async () => {
      const { xaiProvider } = await import('../../ai-layer/explainability/xai-provider.js');
      vi.mocked(xaiProvider.generateEthicsReport).mockReturnValue({
        reportId: 'eth-1', verdict: { bias: 0, privacy: 0, legal: 0, fairness: 0, transparency: 0 },
        recommendations: [], compliance: { dpdp_act: true, it_act_2000: true },
      });

      const res = await invoke(app, 'POST', '/ai/ethics/report', { verdict: {} });
      expect(res.body.report.compliance.dpdp_act).toBe(true);
    });
  });

  describe('POST /ai/models/register', () => {
    it('registers a new model', async () => {
      const res = await invoke(app, 'POST', '/ai/models/register', {
        id: 'custom', name: 'Custom', modalities: ['text'], capabilities: ['analysis'],
      });
      expect(res.body.ok).toBe(true);
    });
  });
});
