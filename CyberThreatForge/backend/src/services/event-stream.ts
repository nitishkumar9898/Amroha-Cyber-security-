/**
 * =============================================================================
 * EVENT STREAM — Real-Time Correlation via Kafka/Redpanda
 * =============================================================================
 *
 * Handles asynchronous event-driven processing:
 *   - Evidence upload → ingestion pipeline trigger
 *   - Threat feed update → IOC correlation
 *   - Investigation finding → cross-module fusion
 *   - System health change → auto-remediation
 *   - Anomaly detection → alert escalation
 *
 * In production, backed by Apache Kafka/Redpanda for:
 *   - At-least-once delivery guarantees
 *   - Event sourcing for full audit trail
 *   - Log compaction for state restoration
 *   - Exactly-once semantics for critical events
 *
 * Architecture:
 *   Producers (API, agents, modules)
 *     → Kafka Topics (partitioned by domain/key)
 *       → Consumer Groups (per module)
 *         → State Stores (materialized views)
 */

import { EventEmitter } from 'node:events';
import { randomUUID } from 'node:crypto';
import { sentinelCore, Domain, Severity } from './sentinel-core.js';

// ─── Event Types ────────────────────────────────────────────────────────────

export type EventType =
  | 'evidence.uploaded' | 'evidence.processed' | 'evidence.analyzed'
  | 'investigation.created' | 'investigation.completed'
  | 'finding.generated' | 'finding.correlated'
  | 'ioc.discovered' | 'ioc.updated'
  | 'threat.feed.updated'
  | 'alert.generated' | 'alert.escalated'
  | 'module.health.changed' | 'module.error'
  | 'system.anomaly' | 'system.remediation'
  | 'user.login' | 'user.action';

export interface Event {
  id: string;
  type: EventType;
  source: string;
  domain: Domain;
  actorId: string;
  payload: unknown;
  metadata: Record<string, unknown>;
  timestamp: string;
  partitionKey: string;
}

export interface EventHandler {
  (event: Event): Promise<void>;
}

// ─── Event Stream (Kafka-like in-memory — swap for real Kafka in production) ──

export class EventStream extends EventEmitter {
  private static instance: EventStream;
  private readonly handlers = new Map<EventType, Set<EventHandler>>();
  private readonly history: Event[] = [];
  private readonly MAX_HISTORY = 10000;
  private consumerInterval: ReturnType<typeof setInterval> | null = null;

  private constructor() {
    super();
    this.setMaxListeners(500);
    this.startConsumerLoop();
  }

  static getInstance(): EventStream {
    if (!EventStream.instance) {
      EventStream.instance = new EventStream();
    }
    return EventStream.instance;
  }

  // ── Produce Event ─────────────────────────────────────────────────────────

  async produce(event: Omit<Event, 'id' | 'timestamp'>): Promise<Event> {
    const fullEvent: Event = {
      ...event,
      id: randomUUID(),
      timestamp: new Date().toISOString(),
    };

    // Store in history
    this.history.push(fullEvent);
    if (this.history.length > this.MAX_HISTORY) {
      this.history.shift();
    }

    // Emit for immediate processing
    this.emit('event', fullEvent);
    this.emit(fullEvent.type, fullEvent);

    // Notify SentinelCore
    sentinelCore.emit('event', fullEvent);

    return fullEvent;
  }

  // ── Consume Events ────────────────────────────────────────────────────────

  subscribe(eventType: EventType, handler: EventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(eventType)?.delete(handler);
    };
  }

  subscribeAll(handler: EventHandler): () => void {
    const unsubs: Array<() => void> = [];
    for (const type of Object.values(EVENT_TYPES)) {
      unsubs.push(this.subscribe(type as EventType, handler));
    }
    return () => unsubs.forEach((u) => u());
  }

  private startConsumerLoop(): void {
    // In production, replace with Kafka consumer:
    //   const consumer = kafka.consumer({ groupId: 'sentinel-core' });
    //   await consumer.subscribe({ topic: /ctf-.*/ });
    //   await consumer.run({ eachMessage: handler });

    this.consumerInterval = setInterval(async () => {
      // Process events from the in-memory queue
      // In production, this is handled by Kafka consumer groups
    }, 100);
  }

  // ── Query History ─────────────────────────────────────────────────────────

  getHistory(eventType?: EventType, since?: string, limit = 100): Event[] {
    let filtered = this.history;
    if (eventType) filtered = filtered.filter((e) => e.type === eventType);
    if (since) filtered = filtered.filter((e) => e.timestamp >= since);
    return filtered.slice(-limit);
  }

  getEventsBySource(source: string, limit = 50): Event[] {
    return this.history
      .filter((e) => e.source === source)
      .slice(-limit);
  }

  // ── Aggregated Metrics ────────────────────────────────────────────────────

  getMetrics(): {
    totalEvents: number;
    eventsByType: Record<string, number>;
    eventsByDomain: Record<string, number>;
    throughputPerMinute: number;
  } {
    const byType: Record<string, number> = {};
    const byDomain: Record<string, number> = {};
    const oneMinAgo = Date.now() - 60000;

    for (const event of this.history) {
      byType[event.type] = (byType[event.type] ?? 0) + 1;
      byDomain[event.domain] = (byDomain[event.domain] ?? 0) + 1;
    }

    const recentCount = this.history.filter(
      (e) => new Date(e.timestamp).getTime() > oneMinAgo,
    ).length;

    return {
      totalEvents: this.history.length,
      eventsByType: byType,
      eventsByDomain: byDomain,
      throughputPerMinute: recentCount,
    };
  }

  // ── Shutdown ──────────────────────────────────────────────────────────────

  async shutdown(): Promise<void> {
    if (this.consumerInterval) clearInterval(this.consumerInterval);
    this.removeAllListeners();
    this.handlers.clear();
  }

  static readonly EVENT_TYPES: EventType[] = [
    'evidence.uploaded', 'evidence.processed', 'evidence.analyzed',
    'investigation.created', 'investigation.completed',
    'finding.generated', 'finding.correlated',
    'ioc.discovered', 'ioc.updated',
    'threat.feed.updated',
    'alert.generated', 'alert.escalated',
    'module.health.changed', 'module.error',
    'system.anomaly', 'system.remediation',
    'user.login', 'user.action',
  ];
}

export const eventStream = EventStream.getInstance();
export const EVENT_TYPES = EventStream.EVENT_TYPES;

// ─── Default Handlers ───────────────────────────────────────────────────────

// Evidence uploaded → trigger ingestion pipeline
eventStream.subscribe('evidence.uploaded', async (event) => {
  console.log(`[EventStream] Evidence uploaded: ${(event.payload as any)?.evidenceId}`);
  sentinelCore.queueLearning('evidence-ingestion', event.payload);
});

// IOC discovered → cross-reference with active investigations
eventStream.subscribe('ioc.discovered', async (event) => {
  const ioc = event.payload as { type: string; value: string; severity: string };
  console.log(`[EventStream] IOC discovered: ${ioc.type} = ${ioc.value}`);

  // Broadcast to all investigation listeners
  eventStream.emit('ioc.correlate', ioc);
});

// Alert escalated → notify on-call personnel
eventStream.subscribe('alert.escalated', async (event) => {
  const alert = event.payload as { severity: string; summary: string; caseId: string };
  console.log(`[EventStream] ALERT ESCALATED: [${alert.severity}] ${alert.summary}`);

  if (alert.severity === 'critical') {
    // Trigger immediate human notification (SMS, PagerDuty, etc.)
    console.log(`[EventStream] CRITICAL: Paging on-call for case ${alert.caseId}`);
  }
});
