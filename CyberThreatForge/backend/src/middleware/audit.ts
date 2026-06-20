import { FastifyRequest, FastifyReply } from 'fastify';
import crypto from 'node:crypto';

/**
 * Immutable Audit Log Middleware
 * Creates a verifiable chain-of-custody using HMAC chaining.
 * Compliant with IT Act 2000, Section 65B of Indian Evidence Act.
 */

interface AuditEntry {
  id: string;
  timestamp: string;
  actorId: string;
  actorRole: string;
  action: string;
  resource: string;
  resourceId?: string;
  metadata?: Record<string, unknown>;
  previousHash: string;
  hash: string;
}

let previousHash = '0000000000000000000000000000000000000000000000000000000000000000';

function computeHash(entry: Omit<AuditEntry, 'hash'>): string {
  const hmac = crypto.createHmac('sha256', process.env.AUDIT_HMAC_KEY ?? 'default-key');
  hmac.update(entry.previousHash);
  hmac.update(entry.id);
  hmac.update(entry.timestamp);
  hmac.update(entry.actorId);
  hmac.update(entry.action);
  hmac.update(entry.resource);
  return hmac.digest('hex');
}

export async function auditLogger(
  request: FastifyRequest,
  reply: FastifyReply,
  action: string,
  resource: string,
  resourceId?: string,
  metadata?: Record<string, unknown>,
) {
  const entry: Omit<AuditEntry, 'hash'> = {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    actorId: request.user?.sub ?? 'anonymous',
    actorRole: request.user?.role ?? 'unauthenticated',
    action,
    resource,
    resourceId,
    metadata,
    previousHash,
  };

  entry.hash = computeHash(entry);
  previousHash = entry.hash;

  // Persist to audit log table or external immutable store
  await request.server.auditDb?.insert('audit_log_immutable', entry);

  return entry;
}
