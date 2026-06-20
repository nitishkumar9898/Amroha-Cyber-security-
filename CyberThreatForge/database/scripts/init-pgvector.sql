-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pgcrypto for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enable table partitioning
CREATE EXTENSION IF NOT EXISTS pg_partman;
