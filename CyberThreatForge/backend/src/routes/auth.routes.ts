import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { requireRole } from '../middleware/auth.js';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  mfaCode: z.string().length(6).optional(),
});

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(12),
  name: z.string().min(2),
  role: z.enum(['police', 'nia', 'cbi', 'researcher']),
  department: z.string(),
  station: z.string().optional(),
});

export async function authRoutes(app: FastifyInstance) {
  app.post('/auth/login', async (request: FastifyRequest, reply: FastifyReply) => {
    const body = loginSchema.parse(request.body);
    const result = await request.server.authService.login(body.email, body.password, body.mfaCode);
    if (!result) return reply.status(401).send({ error: 'Invalid credentials' });
    return reply.send(result);
  });

  app.post('/auth/register', { preHandler: [requireRole('admin', 'super_admin')] }, async (request, reply) => {
    const body = registerSchema.parse(request.body);
    const user = await request.server.authService.register(body);
    return reply.status(201).send(user);
  });

  app.post('/auth/refresh', async (request: FastifyRequest, reply: FastifyReply) => {
    const { refreshToken } = request.body as { refreshToken: string };
    const tokens = await request.server.authService.refresh(refreshToken);
    if (!tokens) return reply.status(401).send({ error: 'Invalid refresh token' });
    return reply.send(tokens);
  });

  app.post('/auth/logout', async (request: FastifyRequest, reply: FastifyReply) => {
    await request.server.authService.logout(request.user.sub);
    return reply.send({ ok: true });
  });

  app.post('/auth/mfa/setup', { preHandler: [requireRole('police', 'nia', 'cbi', 'admin')] }, async (request, reply) => {
    const secret = await request.server.authService.setupMfa(request.user.sub);
    return reply.send(secret);
  });

  app.post('/auth/mfa/verify', { preHandler: [requireRole('police', 'nia', 'cbi', 'admin')] }, async (request, reply) => {
    const { code } = request.body as { code: string };
    const valid = await request.server.authService.verifyMfa(request.user.sub, code);
    return reply.send({ verified: valid });
  });
}
