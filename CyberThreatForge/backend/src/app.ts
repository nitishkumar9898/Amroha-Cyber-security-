/**
 * =============================================================================
 * CyberThreatForge — Application Entry Point
 * =============================================================================
 *
 * Registers all routes, plugins, and initializes the SentinelCore orchestrator
 * with all available modules.
 */

import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import fastifyJwt from '@fastify/jwt';
import fastifyRateLimit from '@fastify/rate-limit';
import multipart from '@fastify/multipart';
import { env } from './config/env.js';
import { connectRedis, redisClient } from './config/redis.js';
import { verifyNeo4jConnection } from './config/neo4j.js';
import { db } from './config/database.js';
import { AuthService } from './services/auth.service.js';
import { sentinelCore } from './services/sentinel-core.js';
import { moduleRegistry } from './services/module-registry.js';
import { pipelineOrchestrator } from './services/pipeline-orchestrator.js';
import { eventStream } from './services/event-stream.js';

// Routes
import { authRoutes } from './routes/auth.routes.js';
import { caseRoutes } from './routes/cases.routes.js';
import { evidenceRoutes } from './routes/evidence.routes.js';
import { aiRoutes } from './routes/ai.routes.js';

async function buildApp() {
  const app = Fastify({
    logger: {
      level: env.NODE_ENV === 'production' ? 'info' : 'debug',
      ...(env.NODE_ENV === 'development' && {
        transport: { target: 'pino-pretty', options: { colorize: true } },
      }),
    },
    bodyLimit: 2 * 1024 * 1024 * 1024, // 2GB for evidence uploads
  });

  // ── Core Plugins ──────────────────────────────────────────────────────────
  await app.register(cors, { origin: true, credentials: true });
  await app.register(helmet, {
    contentSecurityPolicy: false,
    crossOriginEmbedderPolicy: false,
  });
  await app.register(multipart, {
    limits: { fileSize: 2 * 1024 * 1024 * 1024, files: 10 },
  });
  await app.register(fastifyJwt, {
    secret: env.JWT_SECRET,
    sign: { algorithm: 'HS256' },
  });
  await app.register(fastifyRateLimit, {
    max: 100,
    timeWindow: '1 minute',
    redis: redisClient,
  });

  // ── Decorate with services ────────────────────────────────────────────────
  app.decorate('db', db);
  app.decorate('redis', redisClient);
  app.decorate('authService', new AuthService(app));
  app.decorate('sentinelCore', sentinelCore);
  app.decorate('moduleRegistry', moduleRegistry);
  app.decorate('pipelineOrchestrator', pipelineOrchestrator);
  app.decorate('eventStream', eventStream);

  // ── Types for decorated properties ────────────────────────────────────────
  declare module 'fastify' {
    interface FastifyInstance {
      db: typeof db;
      redis: typeof redisClient;
      authService: AuthService;
      sentinelCore: typeof sentinelCore;
      moduleRegistry: typeof moduleRegistry;
      pipelineOrchestrator: typeof pipelineOrchestrator;
      eventStream: typeof eventStream;
    }
  }

  // ── JWT Auth Hook ─────────────────────────────────────────────────────────
  const PUBLIC_PATHS = [
    '/api/v1/auth/login', '/api/v1/auth/register',
    '/api/v1/auth/refresh', '/api/v1/health',
    '/api/v1/auth/mfa/verify',
  ];

  app.decorateRequest('user', null);
  app.addHook('onRequest', async (request) => {
    if (PUBLIC_PATHS.includes(request.url)) return;
    try {
      await request.jwtVerify();
    } catch {
      // Will return 401 from protected routes
    }
  });

  // ── Health Check ──────────────────────────────────────────────────────────
  app.get('/api/v1/health', async () => ({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    modules: moduleRegistry.getPluginCount(),
    activeInvestigations: sentinelCore.getSystemHealth().activeInvestigations,
    eventThroughput: eventStream.getMetrics().throughputPerMinute,
  }));

  // ── Routes ────────────────────────────────────────────────────────────────
  await app.register(
    async (scoped) => {
      await authRoutes(scoped);
      await caseRoutes(scoped);
      await evidenceRoutes(scoped);
      await aiRoutes(scoped);

      // SentinelCore system routes
      scoped.get('/system/modules', async () => ({
        total: moduleRegistry.getPluginCount(),
        capabilities: Object.fromEntries(moduleRegistry.getCapabilityIndex()),
        executionOrder: moduleRegistry.getExecutionOrder(),
      }));

      scoped.get('/system/insights', async (request) => {
        const { domain, limit } = request.query as { domain?: string; limit?: string };
        return sentinelCore.getInsights(
          domain as any,
          limit ? parseInt(limit) : 50,
        );
      });

      scoped.get('/system/events', async (request) => {
        const { type, since, limit } = request.query as { type?: string; since?: string; limit?: string };
        return eventStream.getHistory(
          type as any,
          since,
          limit ? parseInt(limit) : 100,
        );
      });
    },
    { prefix: '/api/v1' },
  );

  // ── Global Error Handler ──────────────────────────────────────────────────
  app.setErrorHandler((error, _request, reply) => {
    app.log.error(error);

    // Zod validation errors
    if (error.name === 'ZodError') {
      return reply.status(400).send({
        error: 'Validation Error',
        details: JSON.parse(error.message),
      });
    }

    // Rate limit
    if (error.statusCode === 429) {
      return reply.status(429).send({ error: 'Too many requests. Try again later.' });
    }

    // Default
    const statusCode = error.statusCode ?? 500;
    return reply.status(statusCode).send({
      error: statusCode === 500 ? 'Internal Server Error' : error.message,
    });
  });

  return app;
}

async function start() {
  try {
    // Connect to infrastructure
    await connectRedis();
    await verifyNeo4jConnection();

    // Initialize SentinelCore
    sentinelCore.registerModule({
      id: 'sentinel-core',
      domain: 'ai_governance',
      version: '2.0.0',
      capabilities: ['orchestration', 'fusion', 'learning', 'ethics'],
      dependencies: [],
      securityClearance: 5,
      status: 'active',
      health: { cpu: 0, memory: 0, uptime: 0 },
    });

    // Initialize Module Registry
    moduleRegistry.on('plugin:registered', ({ id, domain }) => {
      console.log(`[Registry] Plugin loaded: ${id} (${domain})`);
    });

    // Start server
    const app = await buildApp();
    await app.listen({ port: env.APP_PORT, host: '0.0.0.0' });
    console.log(`\n┌──────────────────────────────────────────────┐`);
    console.log(`│  CyberThreatForge v1.0                      │`);
    console.log(`│  Server:   http://localhost:${env.APP_PORT}          │`);
    console.log(`│  Health:   http://localhost:${env.APP_PORT}/api/v1/health │`);
    console.log(`│  Modules:  ${moduleRegistry.getPluginCount()} registered            │`);
    console.log(`└──────────────────────────────────────────────┘\n`);
  } catch (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }
}

start();
