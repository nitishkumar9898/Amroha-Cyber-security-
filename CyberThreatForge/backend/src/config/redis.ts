import { createClient } from 'redis';
import { env } from './env.js';

export const redisClient = createClient({
  socket: {
    host: env.REDIS_HOST,
    port: env.REDIS_PORT,
  },
  password: env.REDIS_PASSWORD || undefined,
});

redisClient.on('error', (err) => console.error('[Redis] Error:', err));
redisClient.on('connect', () => console.log('[Redis] Connection established'));

export async function connectRedis() {
  await redisClient.connect();
}
