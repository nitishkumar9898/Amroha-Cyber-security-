import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { requireRole, requirePermission } from '../middleware/auth.js';

const createCaseSchema = z.object({
  title: z.string().min(3).max(200),
  description: z.string().min(10),
  classification: z.enum(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']),
  type: z.enum(['cyber_crime', 'digital_forensics', 'threat_intel', 'incident_response']),
  jurisdiction: z.string(),
  firNumber: z.string().optional(),
});

export async function caseRoutes(app: FastifyInstance) {
  app.post('/cases', { preHandler: [requireRole('police', 'nia', 'cbi', 'admin')] }, async (request, reply) => {
    const body = createCaseSchema.parse(request.body);
    const caseRecord = await request.server.caseService.create({
      ...body,
      createdBy: request.user.sub,
    });
    return reply.status(201).send(caseRecord);
  });

  app.get('/cases', { preHandler: [requireRole('police', 'nia', 'cbi', 'researcher')] }, async (request, reply) => {
    const { status, page, limit } = request.query as { status?: string; page?: string; limit?: string };
    const result = await request.server.caseService.list({
      status,
      page: Number(page) || 1,
      limit: Number(limit) || 20,
      userRole: request.user.role,
      userId: request.user.sub,
    });
    return reply.send(result);
  });

  app.get('/cases/:id', { preHandler: [requireRole('police', 'nia', 'cbi', 'researcher')] }, async (request, reply) => {
    const { id } = request.params as { id: string };
    const caseRecord = await request.server.caseService.getById(id);
    if (!caseRecord) return reply.status(404).send({ error: 'Case not found' });
    return reply.send(caseRecord);
  });

  app.patch('/cases/:id', { preHandler: [requirePermission('cases:update')] }, async (request, reply) => {
    const { id } = request.params as { id: string };
    const body = request.body as Record<string, unknown>;
    const updated = await request.server.caseService.update(id, body);
    return reply.send(updated);
  });
}
