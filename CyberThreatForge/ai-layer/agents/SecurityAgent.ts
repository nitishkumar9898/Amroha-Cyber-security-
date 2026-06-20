/**
 * Security Agent — Zero-Trust Enforcer & Anomaly Detection
 * Monitors: authentication patterns, access anomalies, data exfiltration attempts
 */

export interface SecurityEvent {
  id: string;
  type: 'auth_anomaly' | 'data_exfil' | 'privilege_escalation' | 'brute_force' | 'geo_anomaly';
  severity: 'low' | 'medium' | 'high' | 'critical';
  actorId: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export class SecurityAgent {
  private readonly rateLimitMap = new Map<string, number[]>();

  analyzeAuthAttempt(email: string, success: boolean, ip: string, userAgent: string): SecurityEvent | null {
    const now = Date.now();
    const attempts = this.rateLimitMap.get(ip) ?? [];
    const recent = attempts.filter((t) => now - t < 300_000); // 5 min window
    recent.push(now);
    this.rateLimitMap.set(ip, recent);

    if (recent.length >= 5 && !success) {
      return {
        id: crypto.randomUUID(),
        type: 'brute_force',
        severity: 'high',
        actorId: email,
        details: { ip, attempts: recent.length, userAgent },
        timestamp: new Date().toISOString(),
      };
    }

    // Geo-anomaly detection (placeholder — integrate with GeoIP)
    if (success && ip !== '127.0.0.1') {
      // Check if IP matches expected jurisdiction
    }

    return null;
  }

  async scanForExfiltration(records: unknown[]): Promise<SecurityEvent[]> {
    const events: SecurityEvent[] = [];
    const batchSize = 100;
    for (let i = 0; i < records.length; i += batchSize) {
      const batch = records.slice(i, i + batchSize);
      if (batch.length > batchSize * 0.8) {
        events.push({
          id: crypto.randomUUID(),
          type: 'data_exfil',
          severity: 'medium',
          actorId: 'system',
          details: { batchSize: batch.length, consecutiveBatches: Math.ceil(records.length / batchSize) },
          timestamp: new Date().toISOString(),
        });
      }
    }
    return events;
  }
}
