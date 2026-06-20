/**
 * =============================================================================
 * SENTINEL AI BRIDGE — Backend <-> AI Layer Integration API
 * =============================================================================
 *
 * Primary integration point between the backend API and the AI layer.
 * Handles:
 *   - Request routing from API routes to SentinelAICore
 *   - Response transformation and caching
 *   - Module <-> AI agent communication
 *   - Continual learning data collection
 *   - XAI explanation requests
 *
 * This bridge ensures the backend (Node.js/Fastify) can seamlessly
 * communicate with the AI layer (Python/PyTorch + TypeScript agents).
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { randomUUID } from 'node:crypto';
import { sentinelAI, AIRequest, Modality } from '../../ai-layer/sentinel-ai-core.js';
import { continualLearning, LearningTrigger } from '../../ai-layer/continual-learning-engine.js';
import { ensembleManager } from '../../ai-layer/models/ensemble-manager.js';
import { xaiProvider, ExplanationLevel } from '../../ai-layer/explainability/xai-provider.js';
import { sentinelCore } from './sentinel-core.js';
import { requireRole } from '../middleware/auth.js';

// ─── Validation Schemas ─────────────────────────────────────────────────────

const analyzeSchema = z.object({
  input: z.union([z.string(), z.record(z.unknown()), z.array(z.unknown())]),
  context: z.object({
    caseId: z.string().uuid().optional(),
    evidenceId: z.string().optional(),
    domain: z.string().optional(),
    requiredCapabilities: z.array(z.string()).optional(),
    confidenceThreshold: z.number().min(0).max(1).optional(),
    requireXAI: z.boolean().optional().default(true),
    temperature: z.number().min(0).max(2).optional(),
    maxTokens: z.number().min(1).max(128000).optional(),
  }),
  modality: z.string().optional(),
});

const explainSchema = z.object({
  analysisId: z.string().uuid(),
  level: z.enum(['shallow', 'standard', 'deep', 'forensic']).default('standard'),
  audience: z.enum(['investigator', 'legal_advisor', 'court', 'system_admin', 'data_subject']).default('investigator'),
  language: z.enum(['en', 'hi']).default('en'),
});

const feedbackSchema = z.object({
  analysisId: z.string().uuid(),
  rating: z.union([z.literal(-1), z.literal(0), z.literal(1)]),
  correction: z.unknown().optional(),
  comments: z.string().max(2000).optional(),
});

const ensemblePredictSchema = z.object({
  ensembleId: z.string(),
  modelOutputs: z.array(z.object({
    modelId: z.string(),
    output: z.unknown(),
    confidence: z.number().min(0).max(1),
  })),
});

// ─── AI Bridge Routes ───────────────────────────────────────────────────────

export async function sentinelAIBridge(app: FastifyInstance) {
  // ── Analyze — Main AI entry point ────────────────────────────────────────

  app.post(
    '/ai/analyze',
    { preHandler: [requireRole('police', 'nia', 'cbi', 'admin', 'researcher')] },
    async (request: FastifyRequest, reply: FastifyReply) => {
      const body = analyzeSchema.parse(request.body);

      const result = await sentinelAI.analyze(body.input, {
        caseId: body.context.caseId,
        evidenceId: body.context.evidenceId,
        domain: body.context.domain as any,
        requiredCapabilities: body.context.requiredCapabilities,
        confidenceThreshold: body.context.confidenceThreshold,
        requireXAI: body.context.requireXAI,
        temperature: body.context.temperature,
        maxTokens: body.context.maxTokens,
      });

      // Log for continual learning
      continualLearning.ingestTrainingExample({
        domain: (body.context.domain ?? 'general') as any,
        modelId: result.modelChain[0] ?? 'unknown',
        input: body.input,
        expectedOutput: result.outputs.map(o => o.output),
        metadata: {
          requestId: result.requestId,
          processingTimeMs: result.processingTimeMs,
          modelsUsed: result.modelChain,
        },
      });

      return reply.send({
        id: result.id,
        requestId: result.requestId,
        outputs: result.outputs.map(o => ({
          type: o.type,
          modelName: o.modelName,
          modelVersion: o.modelVersion,
          output: o.output,
          confidence: o.confidence,
        })),
        fusionResult: result.fusionResult,
        confidence: result.confidence,
        uncertainty: result.uncertainty,
        processingTimeMs: result.processingTimeMs,
        modelChain: result.modelChain,
        ethicsPassed: result.ethicsCheck?.passed,
        requiresHumanReview: result.ethicsCheck?.humanReviewRequired,
        timestamp: result.timestamp,
      });
    },
  );

  // ── Explain — Get XAI explanation for analysis ───────────────────────────

  app.post(
    '/ai/explain',
    { preHandler: [requireRole('police', 'nia', 'cbi', 'admin')] },
    async (request: FastifyRequest, reply: FastifyReply) => {
      const body = explainSchema.parse(request.body);

      // Retrieve cached analysis result
      const analysisId = body.analysisId;

      // In production, fetch from cache/DB
      const explanation = await xaiProvider.explain({
        aiResponse: {
          outputs: [],
          modelChain: [],
          confidence: 0,
        },
        level: body.level,
        audience: body.audience,
        language: body.language,
        includeTechnicalDetails: body.level === 'deep' || body.level === 'forensic',
        includeConfidenceIntervals: body.level !== 'shallow',
      });

      return reply.send(explanation);
    },
  );

  // ── Feedback — Human feedback for RLHF ────────────────────────────────────

  app.post(
    '/ai/feedback',
    { preHandler: [requireRole('police', 'nia', 'cbi', 'admin')] },
    async (request: FastifyRequest, reply: FastifyReply) => {
      const body = feedbackSchema.parse(request.body);

      continualLearning.ingestHumanFeedback({
        userId: request.user.sub,
        rating: body.rating,
        correction: body.correction,
        comments: body.comments,
        timestamp: new Date().toISOString(),
      });

      // Trigger immediate learning if negative feedback
      if (body.rating === -1) {
        setImmediate(() => continualLearning.triggerLearning('feedback'));
      }

      return reply.send({ ok: true, message: 'Feedback recorded. Thank you for improving the AI.' });
    },
  );

  // ── Ensemble Predict — Run ensemble prediction ───────────────────────────

  app.post(
    '/ai/ensemble/predict',
    { preHandler: [requireRole('police', 'nia', 'cbi', 'admin')] },
    async (request: FastifyRequest, reply: FastifyReply) => {
      const body = ensemblePredictSchema.parse(request.body);

      const prediction = await ensembleManager.predict(body.ensembleId, body.modelOutputs);
      return reply.send(prediction);
    },
  );

  // ── Ensemble List — Available ensembles ──────────────────────────────────

  app.get(
    '/ai/ensemble/list',
    { preHandler: [requireRole('police', 'nia', 'cbi', 'admin', 'researcher')] },
    async () => {
      // Return list of registered ensembles with metadata
      return {
        ensembles: [
          { id: 'malware-classification-ensemble', name: 'Malware Classification Ensemble', method: 'weighted_average', models: 3 },
          { id: 'deepfake-ensemble', name: 'Deepfake Detection Ensemble', method: 'hard_voting', models: 3 },
          { id: 'attribution-ensemble', name: 'APT Attribution Ensemble', method: 'bayesian_averaging', models: 3 },
          { id: 'threat-scoring-ensemble', name: 'Threat Scoring Ensemble', method: 'weighted_average', models: 3 },
          { id: 'multi-modal-fusion', name: 'Multi-Modal Fusion Ensemble', method: 'dynamic_selection', models: 3 },
        ],
      };
    },
  );

  // ── Agents List — Available AI agents ────────────────────────────────────

  app.get(
    '/ai/agents',
    { preHandler: [requireRole('police', 'nia', 'cbi', 'admin', 'researcher')] },
    async () => {
      const agents = sentinelAI.findAgents();
      return {
        agents: agents.map(a => ({
          id: a.id,
          name: a.name,
          description: a.description,
          domain: a.domain,
          modelCount: a.modelIds.length,
          inputModalities: a.inputModalities,
          outputModalities: a.outputModalities,
          capabilities: a.capabilities,
        })),
      };
    },
  );

  // ── Models List — Available models ───────────────────────────────────────

  app.get(
    '/ai/models',
    { preHandler: [requireRole('police', 'nia', 'cbi', 'admin', 'researcher')] },
    async () => {
      const models = sentinelAI.findModels();
      return {
        models: models.map(m => ({
          id: m.id,
          name: m.name,
          version: m.version,
          modalities: m.modalities,
          capabilities: m.capabilities,
          accuracy: m.accuracy,
          latencyMs: m.latencyMs,
          type: m.modelType,
          status: m.status,
        })),
      };
    },
  );

  // ── Learning Metrics — Continual learning status ─────────────────────────

  app.get(
    '/ai/learning/metrics',
    { preHandler: [requireRole('admin', 'super_admin')] },
    async () => {
      const clMetrics = continualLearning.getMetrics();
      const aiMetrics = sentinelAI.getMetrics();
      const ensembleAccuracy = ensembleManager.getOverallAccuracy();

      return {
        continualLearning: clMetrics,
        aiCore: aiMetrics,
        ensembleAccuracy,
        latestSnapshot: continualLearning.getLatestSnapshot(),
        configuration: {
          replayBufferSize: clMetrics.replayBufferSize,
          activeAdapters: clMetrics.activeAdapters,
          avgAccuracy: ensembleAccuracy > 0 ? ensembleAccuracy : clMetrics.avgAccuracy,
        },
      };
    },
  );

  // ── Learning Trigger — Force training run ────────────────────────────────

  app.post(
    '/ai/learning/trigger',
    { preHandler: [requireRole('admin', 'super_admin')] },
    async (request: FastifyRequest, reply: FastifyReply) => {
      const { trigger } = request.body as { trigger?: LearningTrigger };
      await continualLearning.triggerLearning(trigger ?? 'manual');
      return reply.send({ ok: true, message: 'Learning cycle triggered' });
    },
  );

  // ── XAI Report — Generate ethics report ───────────────────────────────────

  app.post(
    '/ai/ethics/report',
    { preHandler: [requireRole('admin', 'super_admin')] },
    async (request: FastifyRequest, reply: FastifyReply) => {
      const { verdict } = request.body as { verdict: any };
      const report = xaiProvider.generateEthicsReport(verdict);
      return reply.send({ report });
    },
  );

  // ── Register Module Model — External modules register their AI models ────

  app.post(
    '/ai/models/register',
    { preHandler: [requireRole('admin', 'super_admin')] },
    async (request: FastifyRequest, reply: FastifyReply) => {
      const body = request.body as any;
      sentinelAI.registerModel({
        id: body.id,
        name: body.name,
        version: body.version ?? '1.0.0',
        modalities: body.modalities ?? ['text'],
        capabilities: body.capabilities ?? ['analysis'],
        accuracy: body.accuracy ?? 0.9,
        latencyMs: body.latencyMs ?? 1000,
        maxInputSize: body.maxInputSize ?? 100000,
        requiresGpu: body.requiresGpu ?? false,
        modelType: body.modelType ?? 'classifier',
        status: 'active',
      });
      return reply.status(201).send({ ok: true, id: body.id });
    },
  );
}
