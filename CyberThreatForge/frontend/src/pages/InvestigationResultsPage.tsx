import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Activity, CheckCircle, AlertTriangle, Clock, ArrowRight,
  FileText, Download, Share2, Printer, Shield, Hash
} from 'lucide-react';

interface PipelineStep {
  step: number;
  agent: string;
  action: string;
  duration: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: string;
}

interface Finding {
  moduleId: string;
  domain: string;
  summary: string;
  confidence: number;
  severity: string;
  timestamp: string;
}

export function InvestigationResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [steps] = useState<PipelineStep[]>([
    { step: 1, agent: 'Evidence Ingestion', action: 'Verify & classify evidence', duration: 2340, status: 'completed', output: '3 items ingested' },
    { step: 2, agent: 'Artifact Extraction', action: 'Disk analysis + file carving', duration: 15200, status: 'completed', output: '47 artifacts extracted' },
    { step: 3, agent: 'Vector Embedding', action: 'Generate embeddings (pgvector)', duration: 3800, status: 'completed', output: '1536-dim vectors stored' },
    { step: 4, agent: 'Threat Correlation', action: 'Cross-ref IOCs with feeds', duration: 1200, status: 'completed', output: '12 IOCs matched' },
    { step: 5, agent: 'Graph Correlation', action: 'Link evidence in Neo4j', duration: 800, status: 'completed', output: '8 new edges created' },
    { step: 6, agent: 'APT Attribution', action: 'TTP fingerprinting + actor ID', duration: 4500, status: 'running', output: undefined },
    { step: 7, agent: 'AI Analysis', action: 'LLM summarization + scoring', duration: 0, status: 'pending' },
    { step: 8, agent: 'Report Generation', action: 'Section 65B PDF', duration: 0, status: 'pending' },
  ]);

  const [findings] = useState<Finding[]>([
    { moduleId: 'threat-intel', domain: 'threat_intel', summary: 'C2 infrastructure identified: 3 IPs, 2 domains', confidence: 0.94, severity: 'critical', timestamp: new Date().toISOString() },
    { moduleId: 'malware-analysis', domain: 'malware_analysis', summary: 'Malware classified as LockBit 3.0 variant', confidence: 0.97, severity: 'critical', timestamp: new Date().toISOString() },
    { moduleId: 'darkweb-intel', domain: 'darkweb', summary: 'Ransomware leak site posted — 12GB data claimed', confidence: 0.88, severity: 'high', timestamp: new Date().toISOString() },
    { moduleId: 'apt-hunting', domain: 'apt_hunting', summary: 'TTP match: T1566, T1486, T1041 — aligned with APT29', confidence: 0.76, severity: 'high', timestamp: new Date().toISOString() },
  ]);

  const totalDuration = steps.filter(s => s.status === 'completed').reduce((acc, s) => acc + s.duration, 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Investigation Results</h1>
          <p className="text-sm text-gray-500">
            Pipeline: Standard Investigation · {id?.slice(0, 8)}... · Duration: {(totalDuration / 1000).toFixed(1)}s
          </p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-1 px-3 py-1.5 text-xs bg-gray-800 text-gray-300 rounded hover:bg-gray-700">
            <Download className="w-3 h-3" /> Export
          </button>
          <button className="flex items-center gap-1 px-3 py-1.5 text-xs bg-cyan-600 text-white rounded hover:bg-cyan-500">
            <FileText className="w-3 h-3" /> Generate Report
          </button>
        </div>
      </div>

      {/* Pipeline Progress */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h2 className="text-sm font-medium text-gray-300 mb-4">Pipeline Execution</h2>
        <div className="space-y-2">
          {steps.map((step) => (
            <div key={step.step} className="flex items-center gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                step.status === 'completed' ? 'bg-green-900/50 text-green-400' :
                step.status === 'running' ? 'bg-blue-900/50 text-blue-400 animate-pulse' :
                step.status === 'failed' ? 'bg-red-900/50 text-red-400' :
                'bg-gray-800 text-gray-600'
              }`}>
                {step.status === 'completed' ? <CheckCircle className="w-4 h-4" /> :
                 step.status === 'running' ? <Activity className="w-4 h-4" /> :
                 step.status === 'failed' ? <AlertTriangle className="w-4 h-4" /> :
                 <span className="text-xs">{step.step}</span>}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-200">{step.agent}</span>
                  <span className="text-xs text-gray-500">— {step.action}</span>
                </div>
                {step.output && <p className="text-xs text-gray-600 mt-0.5">{step.output}</p>}
              </div>
              <div className="text-xs text-gray-500">
                {step.duration > 0 ? `${(step.duration / 1000).toFixed(1)}s` : '--'}
              </div>
              <div className={`w-20 text-right text-xs ${
                step.status === 'completed' ? 'text-green-400' :
                step.status === 'running' ? 'text-blue-400' :
                step.status === 'failed' ? 'text-red-400' :
                'text-gray-600'
              }`}>
                {step.status.replace('_', ' ')}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Findings Grid */}
      <div className="grid grid-cols-2 gap-4">
        {findings.map((f, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                  f.severity === 'critical' ? 'bg-red-900/50 text-red-400' :
                  f.severity === 'high' ? 'bg-amber-900/50 text-amber-400' :
                  'bg-blue-900/50 text-blue-400'
                }`}>{f.severity}</span>
                <span className="ml-2 text-xs text-gray-500">{f.domain.replace('_', ' ')}</span>
              </div>
              <span className="text-xs text-gray-500">{(f.confidence * 100).toFixed(0)}%</span>
            </div>
            <p className="text-sm text-gray-200">{f.summary}</p>
            <p className="text-xs text-gray-600 mt-2">Module: {f.moduleId}</p>
          </div>
        ))}
      </div>

      {/* Confidence Score */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-300">Aggregate Confidence</h2>
          <span className="text-lg font-bold text-cyan-400">86.3%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div className="bg-gradient-to-r from-cyan-500 to-green-500 h-2 rounded-full" style={{ width: '86.3%' }} />
        </div>
        <div className="flex justify-between text-xs text-gray-600 mt-2">
          <span>Recommended: Human review if {'>'} 95% for critical findings</span>
          <span>2 findings exceed threshold</span>
        </div>
      </div>
    </div>
  );
}
