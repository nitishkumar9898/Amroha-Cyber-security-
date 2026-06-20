import { FastifyInstance } from 'fastify';
import { sentinelAIBridge } from '../services/sentinel-ai-bridge.js';

export async function aiRoutes(app: FastifyInstance) {
  await sentinelAIBridge(app);
}
