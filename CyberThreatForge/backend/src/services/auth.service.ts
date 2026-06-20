import crypto from 'node:crypto';
import speakeasy from 'speakeasy';
import { db } from '../config/database.js';
import { env } from '../config/env.js';
import type { UserRole, JwtPayload } from '../middleware/auth.js';

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export class AuthService {
  private get jwt(): unknown {
    return (this as any).__jwt;
  }

  constructor(private readonly fastify: any) {}

  async login(email: string, password: string, mfaCode?: string): Promise<AuthTokens | null> {
    const user = await db('users').where({ email }).first();
    if (!user) return null;

    const [storedSalt, storedHash] = user.password_hash.split(':');
    const hash = crypto.pbkdf2Sync(password, storedSalt, 100000, 64, 'sha512').toString('hex');
    if (`${storedSalt}:${hash}` !== user.password_hash) return null;

    if (user.mfa_secret) {
      if (!mfaCode) throw new Error('MFA code required');
      const verified = speakeasy.totp.verify({
        secret: user.mfa_secret,
        encoding: 'base32',
        token: mfaCode,
      });
      if (!verified) return null;
    }

    return this.generateTokens(user);
  }

  async register(data: {
    email: string;
    password: string;
    name: string;
    role: UserRole;
    department: string;
    station?: string;
  }): Promise<{ id: string; email: string; name: string; role: string }> {
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.pbkdf2Sync(data.password, salt, 100000, 64, 'sha512').toString('hex');

    const [user] = await db('users')
      .insert({
        email: data.email,
        name: data.name,
        password_hash: `${salt}:${hash}`,
        role: data.role,
        department: data.department,
        station: data.station,
      })
      .returning(['id', 'email', 'name', 'role']);

    return user;
  }

  async refresh(refreshToken: string): Promise<AuthTokens | null> {
    try {
      const payload = this.fastify.jwt.verify(refreshToken) as JwtPayload;
      const user = await db('users').where({ id: payload.sub }).first();
      if (!user) return null;
      return this.generateTokens(user);
    } catch {
      return null;
    }
  }

  async logout(userId: string): Promise<void> {
    await redisClient.del(`session:${userId}`);
  }

  async setupMfa(userId: string): Promise<{ secret: string; qrCodeUrl: string }> {
    const secret = speakeasy.generateSecret({ name: `CyberThreatForge:${userId}` });
    await db('users').where({ id: userId }).update({ mfa_secret: secret.base32 });
    return {
      secret: secret.base32,
      qrCodeUrl: secret.otpauth_url ?? '',
    };
  }

  async verifyMfa(userId: string, code: string): Promise<boolean> {
    const user = await db('users').where({ id: userId }).first();
    if (!user?.mfa_secret) return false;
    return speakeasy.totp.verify({
      secret: user.mfa_secret,
      encoding: 'base32',
      token: code,
    });
  }

  private generateTokens(user: any): AuthTokens {
    const payload: JwtPayload = {
      sub: user.id,
      role: user.role,
      department: user.department,
      station: user.station,
      permissions: this.getPermissionsForRole(user.role),
    };

    const accessToken = this.fastify.jwt.sign(payload, { expiresIn: env.JWT_ACCESS_EXPIRY });
    const refreshToken = this.fastify.jwt.sign(
      { sub: user.id, type: 'refresh' },
      { expiresIn: env.JWT_REFRESH_EXPIRY },
    );

    return {
      accessToken,
      refreshToken,
      expiresIn: 900, // 15 minutes in seconds
    };
  }

  private getPermissionsForRole(role: UserRole): string[] {
    const permissions: Record<UserRole, string[]> = {
      researcher: ['cases:read', 'evidence:read', 'iocs:read'],
      police: ['cases:read', 'cases:create', 'evidence:read', 'evidence:create', 'iocs:read'],
      nia: [
        'cases:read', 'cases:create', 'cases:update',
        'evidence:read', 'evidence:create', 'evidence:update',
        'iocs:read', 'iocs:create',
      ],
      cbi: [
        'cases:read', 'cases:create', 'cases:update', 'cases:delete',
        'evidence:read', 'evidence:create', 'evidence:update', 'evidence:delete',
        'iocs:read', 'iocs:create', 'iocs:update',
        'users:read',
      ],
      admin: ['*'],
      super_admin: ['*'],
    };
    return permissions[role] ?? [];
  }
}
