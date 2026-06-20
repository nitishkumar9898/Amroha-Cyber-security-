import { FastifyRequest, FastifyReply } from 'fastify';

export type UserRole = 'police' | 'nia' | 'cbi' | 'researcher' | 'admin' | 'super_admin';

export interface JwtPayload {
  sub: string;
  role: UserRole;
  department: string;
  station?: string;
  permissions: string[];
}

declare module 'fastify' {
  interface FastifyRequest {
    user: JwtPayload;
  }
}

export const ROLES_HIERARCHY: Record<UserRole, number> = {
  researcher: 0,
  police: 1,
  nia: 2,
  cbi: 3,
  admin: 4,
  super_admin: 5,
};

export function requireRole(...allowedRoles: UserRole[]) {
  return async (request: FastifyRequest, reply: FastifyReply) => {
    const userRole = request.user?.role;
    if (!userRole || !allowedRoles.includes(userRole)) {
      return reply.status(403).send({ error: 'Insufficient permissions' });
    }
  };
}

export function requirePermission(permission: string) {
  return async (request: FastifyRequest, reply: FastifyReply) => {
    const perms = request.user?.permissions ?? [];
    if (!perms.includes(permission) && request.user?.role !== 'super_admin') {
      return reply.status(403).send({ error: `Missing permission: ${permission}` });
    }
  };
}
