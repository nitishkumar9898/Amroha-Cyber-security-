import { moduleRegistry } from '../../backend/src/services/module-registry.js';
import { sentinelAI } from '../../ai-layer/sentinel-ai-core.js';
import { sentinelCore } from '../../backend/src/services/sentinel-core.js';
import { DeepfakeDetectorPlugin } from './DeepfakeDetectorPlugin.js';
import { MalwareSandboxPlugin } from './MalwareSandboxPlugin.js';
import { MobileIOTForensicsPlugin } from './MobileIOTForensicsPlugin.js';
import { DarkWebIntelPluginV2 } from './DarkWebIntelPlugin.js';
import { CyberPsychologyPlugin } from './CyberPsychologyPlugin.js';
import { OSINTSocialIntelPlugin } from './OSINTSocialIntelPlugin.js';
import { PredictiveAnalyticsPlugin } from './PredictiveAnalyticsPlugin.js';
import { EvidenceCorrelationPlugin } from './EvidenceCorrelationPlugin.js';

export async function registerAllPlugins(): Promise<void> {
  const plugins = [
    new DeepfakeDetectorPlugin(),
    new MalwareSandboxPlugin(),
    new MobileIOTForensicsPlugin(),
    new DarkWebIntelPluginV2(),
    new CyberPsychologyPlugin(),
    new OSINTSocialIntelPlugin(),
    new PredictiveAnalyticsPlugin(),
    new EvidenceCorrelationPlugin(),
  ];

  for (const plugin of plugins) {
    try {
      await plugin.initialize();
      moduleRegistry.registerPlugin(plugin);

      sentinelAI.registerModel({
        id: plugin.manifest.id,
        name: plugin.manifest.id.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        version: plugin.manifest.version,
        modalities: plugin.manifest.capabilities.includes('video-deepfake-detection') ? ['image', 'video', 'audio', 'text'] :
                     plugin.manifest.capabilities.includes('static-analysis') ? ['binary'] :
                     plugin.manifest.capabilities.includes('social-media-collection') ? ['text', 'network'] :
                     plugin.manifest.capabilities.includes('threat-forecasting') ? ['text'] :
                     plugin.manifest.capabilities.includes('graph-correlation') ? ['multi'] :
                     ['text'],
        capabilities: plugin.manifest.capabilities,
        accuracy: 0.88,
        latencyMs: 5000,
        maxInputSize: 500_000_000,
        requiresGpu: true,
        modelType: 'ensemble',
        status: 'active',
      });

      sentinelCore.registerModule({
        id: plugin.manifest.id,
        domain: plugin.manifest.domain,
        version: plugin.manifest.version,
        capabilities: plugin.manifest.capabilities,
        dependencies: plugin.manifest.dependencies,
        securityClearance: plugin.manifest.securityClearance,
        status: 'active',
        health: { cpu: 0, memory: 0, uptime: 0 },
      });

      console.log(`[ModuleRegistry] Registered: ${plugin.manifest.id} v${plugin.manifest.version}`);
    } catch (err) {
      console.error(`[ModuleRegistry] Failed to register ${plugin.manifest.id}:`, err);
    }
  }

  console.log(`[ModuleRegistry] All plugins registered. Total: ${plugins.length}`);
}
