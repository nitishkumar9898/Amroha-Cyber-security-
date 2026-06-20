# CyberThreatForge

**Law Enforcement Cyber Investigation & Threat Intelligence Platform**

A secure, scalable, production-grade platform for digital forensic investigations, cyber threat intelligence, and evidence management — purpose-built for Indian law enforcement agencies (Police, NIA, CBI) with full compliance with the **IT Act 2000**, **DPDP Act 2023**, and **Indian Evidence Act 1872 (Section 65B)**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)               │
│              RBG UI · Dashboard · Evidence Viewer        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / WSS
┌──────────────────────▼──────────────────────────────────┐
│              API Gateway (Fastify + JWT)                  │
│         Auth · RBAC · Rate Limit · Input Validation       │
├─────────────────┬──────────────────┬───────────────────┤
│  Auth Module    │  Case Module     │  Evidence Module   │
│  OAuth2 · MFA   │  CRUD · FIR      │  Ingestion · CoC   │
├─────────────────┼──────────────────┼───────────────────┤
│  Forensic Mod.  │  Threat Intel    │  Reporting Mod.    │
│  Artifacts · TL  │  IOC · Feeds     │  PDF · Legal       │
└──────────┬──────┴─────┬────────────┴────────┬──────────┘
           │            │                    │
┌──────────▼────┐ ┌────▼───────┐ ┌──────────▼──────────┐
│  PostgreSQL    │ │  Neo4j      │ │  Vector DB (pgvector)│
│  Structured    │ │  Graph      │ │  AI Embeddings      │
│  Data + Audit  │ │  Evid. Corr.│ │  Semantic Search    │
└───────┬────────┘ └─────┬──────┘ └──────────┬──────────┘
        │                │                  │
┌───────▼────────────────▼──────────────────▼──────────┐
│            MinIO / S3 (Evidence Blob Storage)          │
│           Encrypted at rest · Versioned · Immutable    │
└───────────────────────────────────────────────────────┘
```

## Directory Structure

```
CyberThreatForge/
├── frontend/                  # React + Vite SPA
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Route pages
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API client (Axios)
│   │   ├── store/             # Zustand state management
│   │   ├── types/             # TypeScript definitions
│   │   └── utils/             # Helper functions
│   └── Dockerfile
├── backend/                   # Fastify (Node.js) API
│   ├── src/
│   │   ├── api/               # API handlers
│   │   ├── config/            # DB, Redis, Neo4j config
│   │   ├── middleware/        # Auth, RBAC, Audit
│   │   ├── models/            # Data models
│   │   ├── routes/            # Route definitions
│   │   ├── services/          # Business logic
│   │   └── utils/             # Utilities
│   ├── tests/
│   └── Dockerfile
├── ai-layer/                  # AI / ML Agents
│   ├── agents/
│   │   ├── DataAgent.ts       # Secure ingestion, PII masking
│   │   ├── SecurityAgent.ts   # Anomaly detection
│   │   └── AIAgent.ts         # LLM analysis, embeddings
│   ├── models/
│   ├── pipelines/
│   └── training/
├── modules/                   # Feature modules
│   ├── auth/                  # Authentication & RBAC
│   ├── chain-of-custody/      # Immutable evidence tracking
│   ├── evidence-ingestion/    # Secure file processing
│   ├── forensic-analysis/     # Artifact extraction
│   ├── threat-intel/          # IOC management, feeds
│   ├── reporting/             # Legal report generation
│   └── visualization/         # Graph & chart components
├── database/
│   ├── migrations/            # Knex schema migrations
│   ├── seeds/                 # Test data seeds
│   └── scripts/               # Init scripts
├── security/
│   ├── policies/              # Data classification policy
│   ├── encryption/            # AES-256-GCM service
│   └── audit/                 # Audit configuration
├── deployment/
│   ├── docker/                # Nginx, Dockerfiles
│   ├── kubernetes/            # K8s manifests
│   └── terraform/             # AWS IaC
├── tests/
│   ├── e2e/
│   ├── integration/
│   └── unit/
├── docker-compose.yml         # Local dev environment
├── .env.example               # Environment variables
└── .github/workflows/         # CI/CD pipelines
```

## Key Features

| Feature | Status | Compliance |
|---------|--------|-----------|
| RBAC (Police/NIA/CBI/Researcher/Admin) | ✅ | IT Act 2000 |
| JWT + OAuth2 + MFA (TOTP) | ✅ | ISO 27001 |
| Secure Evidence Ingestion | ✅ | DPDP Act 2023 |
| Chain-of-Custody (HMAC + Digital Signatures) | ✅ | Indian Evidence Act Sec 65B |
| Immutable Audit Log | ✅ | IT Act Sec 3 |
| AES-256-GCM Encryption at Rest | ✅ | ISO 27001 |
| PII Masking & Differential Privacy | ✅ | DPDP Act 2023 |
| Graph-Based Evidence Correlation (Neo4j) | ✅ | — |
| Vector Embeddings & Semantic Search (pgvector) | ✅ | — |
| Dark Web Monitoring (TOR Proxy) | 🔄 | — |
| Forensic Artifact Analysis | 🔄 | — |
| STIX/TAXII Threat Intel Feeds | 🔄 | — |

## Quick Start

### Prerequisites
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 16 (or use Docker)
- Neo4j 5 (or use Docker)

### Local Development

```bash
# 1. Clone & configure
cp .env.example .env
# Edit .env with your secrets

# 2. Start infrastructure
docker compose up -d postgres neo4j redis minio

# 3. Install & run backend
cd backend
npm install
npm run migrate
npm run dev

# 4. Install & run frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Using Docker Compose (full stack)

```bash
docker compose up -d
# Frontend: http://localhost:5173
# Backend API: http://localhost:3000
# MinIO Console: http://localhost:9001
# Neo4j Browser: http://localhost:7474
```

### Production (Kubernetes)

```bash
kubectl apply -f deployment/kubernetes/
# Or use Terraform for full AWS EKS deployment
cd deployment/terraform
terraform init && terraform apply
```

## Security & Compliance

### Role-Based Access Control
| Role | Permissions |
|------|------------|
| **Researcher** | Read-only: cases, evidence, IOCs |
| **Police** | CRUD own cases, upload evidence |
| **NIA** | Full case management, cross-jurisdiction access |
| **CBI** | System-wide access, user management |
| **Admin** | Configuration, audit logs, user management |
| **Super Admin** | Full system access |

### Data Protection (DPDP Act 2023)
- Automatic PII masking during ingestion
- Differential privacy for analytics
- Consent-based data processing
- Right to erasure (data retention policies)
- Data classification: Critical / High / Medium / Low

### Chain of Custody (Indian Evidence Act Sec 65B)
- HMAC-SHA256 chained hash audit trail
- Digital signatures for non-repudiation
- Neo4j graph for visual chain verification
- Tamper-evident with break-point detection

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand |
| Backend | Fastify 4, Node.js 20, TypeScript |
| Database | PostgreSQL 16 + pgvector, Neo4j 5, Redis 7 |
| Auth | JWT (HS256), OAuth2, TOTP (Speakeasy) |
| AI/ML | OpenAI GPT-4, text-embedding-3-small, LangChain |
| Storage | MinIO / S3 (AES-256 encrypted) |
| Infra | Docker, Kubernetes, Terraform (AWS EKS) |
| Monitoring | Sentry, Prometheus, Grafana |

## Next Actions (Phase 2)

1. **Implement forensic analysis tools** — Integrate Sleuth Kit, Volatility 3, YARA scanning
2. **Dark web monitoring agent** — TOR SOCKS5 proxy integration, automated crawling
3. **Threat feed automation** — MISP, AlienVault OTX, STIX/TAXII polling
4. **Advanced visualization** — Neo4j graph explorer, timeline visualizer, MITRE ATT&CK heatmap
5. **Reporting engine** — Auto-generate court-admissible PDF reports with chain-of-custody annex
6. **AI correlation pipeline** — Real-time evidence -> embedding -> Neo4j link prediction
7. **Performance benchmarks** — Load testing with k6, optimize pgvector indexes
8. **Penetration testing** — Third-party security audit before production

## License

MIT — See [LICENSE](LICENSE)
