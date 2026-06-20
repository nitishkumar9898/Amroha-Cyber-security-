import { defineConfig } from 'vitest/config';
import path from 'node:path';

const aiLayerDir = path.resolve(__dirname, '..', 'ai-layer');

export default defineConfig({
  resolve: {
    alias: {
      '../../ai-layer/sentinel-ai-core.js': path.join(aiLayerDir, 'sentinel-ai-core.ts'),
      '../../ai-layer/continual-learning-engine.js': path.join(aiLayerDir, 'continual-learning-engine.ts'),
      '../../ai-layer/models/ensemble-manager.js': path.join(aiLayerDir, 'models', 'ensemble-manager.ts'),
      '../../ai-layer/explainability/xai-provider.js': path.join(aiLayerDir, 'explainability', 'xai-provider.ts'),
    },
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    server: {
      fs: { allow: ['..'] },
    },
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],
      exclude: ['src/**/*.d.ts', 'src/**/*.test.ts'],
      thresholds: {
        statements: 60,
        branches: 50,
        functions: 60,
        lines: 60,
      },
    },
    testTimeout: 30000,
    hookTimeout: 30000,
    sequence: {
      concurrent: false,
    },
  },
});
