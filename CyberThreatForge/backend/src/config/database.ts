import knex from 'knex';
import { env } from './env.js';

export const db = knex({
  client: 'pg',
  connection: {
    host: env.POSTGRES_HOST,
    port: env.POSTGRES_PORT,
    database: env.POSTGRES_DB,
    user: env.POSTGRES_USER,
    password: env.POSTGRES_PASSWORD,
    ssl: env.NODE_ENV === 'production' ? { rejectUnauthorized: true } : false,
  },
  pool: { min: 2, max: 10 },
  migrations: {
    directory: '../../database/migrations',
    extension: 'ts',
  },
  seeds: {
    directory: '../../database/seeds',
    extension: 'ts',
  },
});
