import neo4j from 'neo4j-driver';
import { env } from './env.js';

export const neo4jDriver = neo4j.driver(
  env.NEO4J_URI,
  neo4j.auth.basic(env.NEO4J_USER, env.NEO4J_PASSWORD),
  {
    maxConnectionPoolSize: 10,
    connectionTimeout: 30000,
  },
);

export async function verifyNeo4jConnection() {
  const session = neo4jDriver.session();
  try {
    await session.run('RETURN 1 AS ok');
    console.log('[Neo4j] Connection established');
  } finally {
    await session.close();
  }
}

process.on('exit', () => neo4jDriver.close());
