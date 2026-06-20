/**
 * AI Agent — Orchestrates ML models for threat detection, correlation, and analysis
 */

import OpenAI from 'openai';

export interface AnalysisResult {
  summary: string;
  confidence: number;
  iocs: string[];
  mitreTactics: string[];
  suggestedActions: string[];
}

export class AIAgent {
  private openai: OpenAI;

  constructor(apiKey: string) {
    this.openai = new OpenAI({ apiKey });
  }

  async analyzeEvidence(text: string, context: string): Promise<AnalysisResult> {
    const response = await this.openai.chat.completions.create({
      model: 'gpt-4-turbo',
      messages: [
        {
          role: 'system',
          content: `You are a cyber forensic AI assistant for Indian law enforcement.
Analyze the following evidence and provide:
1. A concise summary
2. Confidence score (0-1)
3. Extracted IOCs (IPs, domains, hashes, emails)
4. MITRE ATT&CK tactics identified
5. Suggested investigation actions

Comply with IT Act 2000 and DPDP Act 2023. Do not expose PII.`,
        },
        { role: 'user', content: `Context: ${context}\n\nEvidence:\n${text}` },
      ],
      temperature: 0.1,
      response_format: { type: 'json_object' },
    });

    const result = JSON.parse(response.choices[0]?.message.content ?? '{}') as AnalysisResult;
    return result;
  }

  async generateEmbedding(text: string): Promise<number[]> {
    const response = await this.openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: text,
    });
    return response.data[0]?.embedding ?? [];
  }

  async correlateEvidence(embeddings: number[][]): Promise<Array<{ sourceIdx: number; targetIdx: number; similarity: number }>> {
    const correlations: Array<{ sourceIdx: number; targetIdx: number; similarity: number }> = [];
    for (let i = 0; i < embeddings.length; i++) {
      for (let j = i + 1; j < embeddings.length; j++) {
        const similarity = this.cosineSimilarity(embeddings[i]!, embeddings[j]!);
        if (similarity > 0.75) {
          correlations.push({ sourceIdx: i, targetIdx: j, similarity });
        }
      }
    }
    return correlations.sort((a, b) => b.similarity - a.similarity);
  }

  private cosineSimilarity(a: number[], b: number[]): number {
    let dot = 0, normA = 0, normB = 0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i]! * b[i]!;
      normA += a[i]! * a[i]!;
      normB += b[i]! * b[i]!;
    }
    return dot / (Math.sqrt(normA) * Math.sqrt(normB));
  }
}
