import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Shield, Clock, User, AlertTriangle, FileText,
  Activity, GitBranch, Download, Lock, ChevronRight, ExternalLink
} from 'lucide-react';

interface CaseDetail {
  id: string;
  title: string;
  description: string;
  classification: string;
  type: string;
  status: string;
  jurisdiction: string;
  fir_number: string | null;
  created_by: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

interface EvidenceItem {
  id: string;
  evidence_type: string;
  description: string;
  file_size: number;
  file_hash: string;
  mime_type: string;
  created_at: string;
}

const TABS = ['Overview', 'Evidence', 'Timeline', 'Chain of Custody', 'Analysis', 'Reports'] as const;

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [activeTab, setActiveTab] = useState<typeof TABS[number]>('Overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        // In production: api.get(`/cases/${id}`), api.get(`/evidence/case/${id}`)
        setCaseData({
          id: id!, title: 'Ransomware Investigation — Govt Portal Defacement',
          description: 'Investigation into the ransomware attack on the state government portal. Evidence includes network captures, memory dumps, and malware samples.',
          classification: 'CRITICAL', type: 'cyber_crime', status: 'under_investigation',
          jurisdiction: 'Cyber Crime PS, New Delhi', fir_number: 'FIR-2026-0421',
          created_by: 'a1b2c3d4', assigned_to: null,
          created_at: '2026-06-15T10:30:00Z', updated_at: '2026-06-20T08:15:00Z',
        });
        setEvidenceList([
          { id: 'e1', evidence_type: 'memory_dump', description: 'RAM dump from infected server', file_size: 4294967296, file_hash: 'sha256:a1b2...', mime_type: 'application/octet-stream', created_at: '2026-06-15T11:00:00Z' },
          { id: 'e2', evidence_type: 'network_capture', description: 'PCAP of C2 communication', file_size: 104857600, file_hash: 'sha256:c3d4...', mime_type: 'application/vnd.tcpdump.pcap', created_at: '2026-06-15T11:05:00Z' },
          { id: 'e3', evidence_type: 'malware_sample', description: 'Ransomware binary extracted', file_size: 5242880, file_hash: 'sha256:e5f6...', mime_type: 'application/x-dosexec', created_at: '2026-06-15T14:30:00Z' },
        ]);
      } catch { /* */ }
      setLoading(false);
    };
    fetch();
  }, [id]);

  if (loading) return <div className="p-6 text-gray-600">Loading case...</div>;
  if (!caseData) return <div className="p-6 text-red-400">Case not found</div>;

  return (
    <div className="p-6 space-y-6">
      {/* Back + Header */}
      <div className="space-y-4">
        <Link to="/cases" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-300">
          <ArrowLeft className="w-4 h-4" /> Back to Cases
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-xl font-bold text-gray-100">{caseData.title}</h1>
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-900/50 text-blue-400">
                {caseData.status.replace('_', ' ')}
              </span>
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-900/50 text-red-400">
                {caseData.classification}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1"><Shield className="w-3 h-3" />{caseData.jurisdiction}</span>
              {caseData.fir_number && <span className="flex items-center gap-1">FIR: {caseData.fir_number}</span>}
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" />Created {new Date(caseData.created_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-1 px-3 py-1.5 text-xs bg-gray-800 text-gray-300 rounded hover:bg-gray-700">
              <Lock className="w-3 h-3" /> Classify
            </button>
            <button className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-500">
              <Activity className="w-3 h-3" /> Launch Investigation
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded text-sm transition-colors ${
              activeTab === tab ? 'bg-cyan-600 text-white' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'Overview' && (
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Description</h3>
              <p className="text-sm text-gray-400">{caseData.description}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Key Findings</h3>
              <div className="space-y-2">
                {[
                  { label: 'C2 Infrastructure', value: '3 IPs · 2 domains · 1 TOR hidden service', severity: 'high' },
                  { label: 'Malware Family', value: 'LockBit 3.0 variant with custom encryption', severity: 'critical' },
                  { label: 'Initial Access', value: 'Phishing email with malicious macro', severity: 'medium' },
                  { label: 'Data Exfiltrated', value: '~50GB including PII of 12,000 citizens', severity: 'critical' },
                ].map((f, i) => (
                  <div key={i} className="flex items-start justify-between p-2 bg-gray-800/50 rounded">
                    <div>
                      <p className="text-xs text-gray-400">{f.label}</p>
                      <p className="text-sm text-gray-200">{f.value}</p>
                    </div>
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                      f.severity === 'critical' ? 'bg-red-900/50 text-red-400' :
                      f.severity === 'high' ? 'bg-amber-900/50 text-amber-400' :
                      'bg-blue-900/50 text-blue-400'
                    }`}>{f.severity}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Case Info</h3>
              <dl className="space-y-2 text-xs">
                <div className="flex justify-between"><dt className="text-gray-500">Type</dt><dd className="text-gray-300">{caseData.type.replace('_', ' ')}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">Evidence Items</dt><dd className="text-gray-300">{evidenceList.length}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">Investigations</dt><dd className="text-gray-300">2</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">Created By</dt><dd className="text-gray-300">{caseData.created_by?.slice(0, 8)}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">Last Updated</dt><dd className="text-gray-300">{new Date(caseData.updated_at).toLocaleString()}</dd></div>
              </dl>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button className="flex items-center gap-2 w-full px-3 py-2 text-xs bg-gray-800 text-gray-300 rounded hover:bg-gray-700">
                  <FileText className="w-3 h-3" /> Generate Section 65B Certificate
                </button>
                <button className="flex items-center gap-2 w-full px-3 py-2 text-xs bg-gray-800 text-gray-300 rounded hover:bg-gray-700">
                  <GitBranch className="w-3 h-3" /> Visualize Evidence Graph
                </button>
                <button className="flex items-center gap-2 w-full px-3 py-2 text-xs bg-gray-800 text-gray-300 rounded hover:bg-gray-700">
                  <Download className="w-3 h-3" /> Export Case Package
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Evidence' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-300">Evidence Inventory ({evidenceList.length})</h3>
            <button className="px-3 py-1.5 text-xs bg-cyan-600 text-white rounded hover:bg-cyan-500">+ Upload Evidence</button>
          </div>
          <div className="divide-y divide-gray-800">
            {evidenceList.map((ev) => (
              <div key={ev.id} className="p-4 hover:bg-gray-800/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-200">{ev.description}</span>
                      <span className="px-1.5 py-0.5 rounded text-xs bg-gray-800 text-gray-400">{ev.evidence_type}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-600">
                      <span>{ev.mime_type}</span>
                      <span>{(ev.file_size / 1024 / 1024).toFixed(1)} MB</span>
                      <span className="font-mono">{ev.file_hash.slice(0, 16)}...</span>
                      <span>{new Date(ev.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-600" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'Chain of Custody' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500">
          <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Chain of Custody — HMAC-chained, digitally signed, tamper-evident</p>
          <p className="text-xs text-gray-600 mt-1">All evidence access and transfers recorded with cryptographic verification</p>
        </div>
      )}

      {activeTab === 'Analysis' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-3">AI Analysis Results</h3>
            <div className="space-y-3 text-sm text-gray-400">
              <p><span className="text-gray-300 font-medium">Confidence:</span> 92.3% — Ransomware attack (LockBit 3.0 variant)</p>
              <p><span className="text-gray-300 font-medium">APTs Mapped:</span> 3 TTPs match APT29 (Cozy Bear) infrastructure patterns</p>
              <p><span className="text-gray-300 font-medium">IOCs Extracted:</span> 12 IPs, 4 domains, 6 file hashes</p>
              <p><span className="text-gray-300 font-medium">MITRE ATT&CK:</span> T1566 (Phishing), T1486 (Data Encrypted), T1041 (Exfiltration Over C2)</p>
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Predictive Scoring</h3>
            <div className="space-y-3 text-sm text-gray-400">
              <p><span className="text-gray-300 font-medium">Escalation Risk:</span> 87% — High likelihood of data being auctioned</p>
              <p><span className="text-gray-300 font-medium">Attribution Confidence:</span> 76% — State-sponsored group likely</p>
              <p><span className="text-gray-300 font-medium">Next Expected Move:</span> Data leak within 72 hours if ransom unpaid</p>
              <p><span className="text-gray-300 font-medium">Recommended Action:</span> Engage CERT-In, prepare breach notification</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Reports' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500">
          <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Case Reports — Court-admissible, Section 65B compliant</p>
          <p className="text-xs text-gray-600 mt-1">Generate investigation summary, forensic report, chain of custody, or expert opinion PDF</p>
        </div>
      )}
    </div>
  );
}
