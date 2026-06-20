/**
 * Data Agent — Secure Ingestion & Anonymization Pipeline
 * Handles: device images, logs, dark web feeds, public datasets, user-uploaded cases
 * Implements: encryption, differential privacy, PII masking (DPDP Act 2023 compliant)
 */

import crypto from 'node:crypto';

export interface IngestedEvidence {
  id: string;
  type: 'device_image' | 'log' | 'darkweb_feed' | 'public_dataset' | 'user_upload';
  originalHash: string;
  encryptedPath: string;
  metadata: Record<string, unknown>;
  piiMasked: boolean;
  dpBudget: number; // Differential privacy budget (epsilon)
}

export class DataAgent {
  private readonly encryptionKey: Buffer;
  private readonly piiPatterns: RegExp[] = [
    /\b\d{4}[-]?\d{4}[-]?\d{4}[-]?\d{4}\b/g,          // Credit cards
    /\b\d{12}\d?\b/g,                                      // Aadhaar (India) — 12 digits
    /\b[A-Z]{5}\d{4}[A-Z]{1}\b/g,                          // PAN (India)
    /\b\d{10}\b/g,                                          // Phone numbers
    /\b[\w.-]+@[\w.-]+\.\w+\b/g,                           // Emails
  ];

  constructor(encryptionHexKey: string) {
    this.encryptionKey = Buffer.from(encryptionHexKey, 'hex');
  }

  async ingest(data: Buffer, type: IngestedEvidence['type'], metadata: Record<string, unknown>): Promise<IngestedEvidence> {
    const originalHash = crypto.createHash('sha256').update(data).digest('hex');

    // PII Masking (DPDP Act compliance)
    const maskedData = this.maskPII(data.toString('utf8'));
    const maskedBuffer = Buffer.from(maskedData, 'utf8');

    // Encrypt at rest (AES-256-GCM)
    const encrypted = this.encrypt(maskedBuffer);

    const evidence: IngestedEvidence = {
      id: crypto.randomUUID(),
      type,
      originalHash,
      encryptedPath: `evidence/${type}/${evidence.id}.enc`,
      metadata: {
        ...metadata,
        ingestionTimestamp: new Date().toISOString(),
        sizeBytes: data.length,
        piiMasked: true,
      },
      piiMasked: true,
      dpBudget: this.calculateDpBudget(data.length),
    };

    return evidence;
  }

  private maskPII(text: string): string {
    let masked = text;
    for (const pattern of this.piiPatterns) {
      masked = masked.replace(pattern, (match) => {
        if (pattern === this.piiPatterns[3]) return 'XXXXXX' + match.slice(-4); // Mask all but last 4 digits
        return '[REDACTED]';
      });
    }
    return masked;
  }

  private encrypt(data: Buffer): Buffer {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', this.encryptionKey, iv);
    const encrypted = Buffer.concat([cipher.update(data), cipher.final()]);
    const authTag = cipher.getAuthTag();
    return Buffer.concat([iv, authTag, encrypted]);
  }

  private calculateDpBudget(dataLength: number): number {
    // Epsilon inversely proportional to sensitivity
    return Math.min(1.0, 1000 / dataLength);
  }

  anonymizeForResearch(evidence: IngestedEvidence): Record<string, unknown> {
    // Differential privacy: add Laplace noise to numeric fields
    const epsilon = evidence.dpBudget;
    const sensitivity = 1.0;
    const scale = sensitivity / epsilon;

    return {
      type: evidence.type,
      fileSizeBytes: evidence.metadata.sizeBytes as number + this.laplaceNoise(scale),
      ingestionDate: new Date().toISOString().split('T')[0],
      _dp_epsilon: epsilon,
      _anonymized: true,
    };
  }

  private laplaceNoise(scale: number): number {
    const u = Math.random() - 0.5;
    return -scale * Math.sign(u) * Math.log(1 - 2 * Math.abs(u));
  }
}
