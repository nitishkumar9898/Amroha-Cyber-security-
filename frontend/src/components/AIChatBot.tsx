import React, { useState, useRef, useEffect } from 'react';
import './AIChatBot.css';

interface Message {
  id: string;
  sender: 'user' | 'sentinel';
  text: string;
  timestamp: string;
  intent?: string;
  confidence?: number;
  threatScore?: number;
  severity?: string;
  agentUsed?: string;
  xaiTrace?: any;
  guardrailFlags?: any[];
  attachmentsProcessed?: number;
  processingTime?: number;
}

interface Attachment {
  file: File;
  preview?: string;
  type: string;
}

export const AIChatBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'sentinel',
      text: 'Greetings, Investigator. I am **SentinelCore v2.0** — your self-evolving, multi-modal AI orchestrator. I process text, images, audio, video, and binary evidence through specialized investigation agents.\n\nMy capabilities include:\n• 🦠 Malware sandbox analysis\n• 🎭 Deepfake detection\n• 📱 Mobile forensics\n• 🌐 Dark web intelligence\n• 🧠 Cyber psychology profiling\n• 🛡️ Autonomous threat remediation\n\nAll responses include full XAI (Explainable AI) traces for transparency. How may I assist your investigation?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [showXaiPanel, setShowXaiPanel] = useState(false);
  const [activeXai, setActiveXai] = useState<any>(null);
  const [showAgentStatus, setShowAgentStatus] = useState(false);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Fetch system status on open
  useEffect(() => {
    if (isOpen && !systemStatus) {
      fetch('/api/sentinel/status')
        .then(r => r.json())
        .then(setSystemStatus)
        .catch(() => {});
    }
  }, [isOpen]);

  const handleSend = async () => {
    if (!inputText.trim() && attachments.length === 0) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: inputText || `[${attachments.length} file(s) attached for analysis]`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachmentsProcessed: attachments.length,
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputText;
    const currentAttachments = [...attachments];
    setInputText('');
    setAttachments([]);
    setIsTyping(true);

    try {
      let data: any;

      if (currentAttachments.length > 0) {
        // Multi-modal request with file uploads
        const formData = new FormData();
        formData.append('message', currentInput || 'Analyze these files');
        currentAttachments.forEach(att => formData.append('files', att.file));

        const response = await fetch('/api/sentinel/multimodal', {
          method: 'POST',
          body: formData,
        });
        data = await response.json();
      } else {
        // Text-only request
        const response = await fetch(`/api/chat?message=${encodeURIComponent(currentInput)}`, {
          method: 'POST',
        });
        data = await response.json();
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'sentinel',
        text: data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: data.intent,
        confidence: data.confidence,
        threatScore: data.threat_score,
        severity: data.severity,
        agentUsed: data.agent_used,
        xaiTrace: data.xai_trace,
        guardrailFlags: data.guardrail_flags,
        attachmentsProcessed: data.attachments_processed,
        processingTime: data.processing_time_ms,
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'sentinel',
        text: '⚠️ **Neural Link Interrupted.** Cannot reach SentinelCore backend. Ensure the API server is running and try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newAttachments: Attachment[] = [];
    Array.from(files).forEach(file => {
      const att: Attachment = { file, type: file.type.split('/')[0] || 'file' };
      if (file.type.startsWith('image/')) {
        att.preview = URL.createObjectURL(file);
      }
      newAttachments.push(att);
    });

    setAttachments(prev => [...prev, ...newAttachments]);
    e.target.value = '';
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const getSeverityClass = (severity?: string) => {
    switch (severity) {
      case 'CRITICAL': return 'severity-critical';
      case 'HIGH': return 'severity-high';
      case 'MEDIUM': return 'severity-medium';
      case 'LOW': return 'severity-low';
      default: return 'severity-info';
    }
  };

  const getAgentIcon = (agent?: string) => {
    switch (agent) {
      case 'orchestrator': return '🎯';
      case 'intelligence': return '🌐';
      case 'forensics': return '🔬';
      case 'action': return '🛡️';
      default: return '🤖';
    }
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'image': return '🖼️';
      case 'audio': return '🎵';
      case 'video': return '🎬';
      case 'application': return '📦';
      default: return '📄';
    }
  };

  const renderFormattedText = (text: string) => {
    // Basic markdown-like formatting
    const lines = text.split('\n');
    return lines.map((line, i) => {
      // Bold
      let formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      // Bullet points
      if (formatted.startsWith('•') || formatted.startsWith('-')) {
        return <div key={i} className="chat-list-item" dangerouslySetInnerHTML={{ __html: formatted }} />;
      }
      // Headers
      if (formatted.startsWith('**') && formatted.endsWith('**')) {
        return <div key={i} className="chat-header-line" dangerouslySetInnerHTML={{ __html: formatted }} />;
      }
      // Numbered items
      if (/^\d+\./.test(formatted)) {
        return <div key={i} className="chat-list-item" dangerouslySetInnerHTML={{ __html: formatted }} />;
      }
      // Code blocks
      if (formatted.startsWith('`') && formatted.endsWith('`')) {
        return <code key={i} className="chat-inline-code">{formatted.slice(1, -1)}</code>;
      }
      // Horizontal rule
      if (formatted.startsWith('---')) {
        return <hr key={i} className="chat-hr" />;
      }
      // Empty lines
      if (formatted.trim() === '') {
        return <div key={i} className="chat-spacer" />;
      }
      return <div key={i} dangerouslySetInnerHTML={{ __html: formatted }} />;
    });
  };

  return (
    <div className={`chat-bot-container ${isOpen ? 'open' : 'closed'} ${isExpanded ? 'expanded' : ''}`}>
      {!isOpen && (
        <button className="chat-bot-toggle" onClick={() => setIsOpen(true)} id="sentinel-toggle">
          <span className="toggle-pulse" />
          <span className="toggle-icon">🤖</span>
          <span className="toggle-text">SentinelCore AI</span>
        </button>
      )}

      {isOpen && (
        <div className="chat-bot-window glass-panel" id="sentinel-window">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-title">
              <span className="status-dot active" />
              <span className="header-text">SentinelCore AI</span>
              <span className="version-badge">v2.0</span>
            </div>
            <div className="header-actions">
              <button
                className={`header-btn ${showAgentStatus ? 'active' : ''}`}
                onClick={() => setShowAgentStatus(!showAgentStatus)}
                title="Agent Status"
              >
                👥
              </button>
              <button
                className={`header-btn ${showXaiPanel ? 'active' : ''}`}
                onClick={() => setShowXaiPanel(!showXaiPanel)}
                title="XAI Traces"
              >
                🔍
              </button>
              <button
                className="header-btn"
                onClick={() => setIsExpanded(!isExpanded)}
                title={isExpanded ? 'Collapse' : 'Expand'}
              >
                {isExpanded ? '⊟' : '⊞'}
              </button>
              <button className="close-btn" onClick={() => { setIsOpen(false); setIsExpanded(false); }}>×</button>
            </div>
          </div>

          {/* System Status Bar */}
          {systemStatus && (
            <div className="system-status-bar">
              <span className="status-item">
                <span className="status-indicator online" /> {systemStatus.status}
              </span>
              <span className="status-item">🧠 Memory: {systemStatus.memory_entries}</span>
              <span className="status-item">🔄 Learning: {systemStatus.continual_learning}</span>
              <span className="status-item">🌐 Nodes: {systemStatus.federated_nodes}</span>
            </div>
          )}

          {/* Agent Status Panel */}
          {showAgentStatus && (
            <div className="agent-status-panel">
              <div className="panel-title">🤖 Investigation Agents</div>
              <div className="agent-grid">
                {['orchestrator', 'intelligence', 'forensics', 'action'].map(agent => (
                  <div key={agent} className="agent-card">
                    <span className="agent-icon">{getAgentIcon(agent)}</span>
                    <span className="agent-name">{agent}</span>
                    <span className="agent-status-badge online">ONLINE</span>
                  </div>
                ))}
              </div>
              <div className="panel-subtitle">📡 Multi-Modal Pipelines</div>
              <div className="pipeline-tags">
                {['🖼️ Image/VLM', '🎵 Audio/ASR', '🎬 Video', '📦 Binary', '📄 Document', '🗄️ Database'].map(p => (
                  <span key={p} className="pipeline-tag">{p}</span>
                ))}
              </div>
            </div>
          )}

          {/* XAI Trace Panel */}
          {showXaiPanel && activeXai && (
            <div className="xai-panel">
              <div className="panel-title">🔍 Explainable AI Trace — {activeXai.trace_id}</div>
              <div className="xai-steps">
                {activeXai.chain_of_thought?.map((step: any, i: number) => (
                  <div key={i} className="xai-step">
                    <div className="xai-step-number">{step.step}</div>
                    <div className="xai-step-content">
                      <div className="xai-step-action">{step.action}</div>
                      <div className="xai-step-result">{step.result}</div>
                      <div className="xai-step-evidence">{step.evidence}</div>
                    </div>
                  </div>
                ))}
              </div>
              {activeXai.mitre_mapping?.length > 0 && (
                <div className="xai-mitre">
                  <span className="mitre-label">MITRE ATT&CK:</span>
                  {activeXai.mitre_mapping.map((t: string, i: number) => (
                    <span key={i} className="mitre-tag">{t}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Main layout: messages + optional side panel */}
          <div className="chat-body-layout">
            {/* Chat Messages */}
            <div className="chat-messages">
              {messages.map((msg) => (
                <div key={msg.id} className={`chat-bubble-container ${msg.sender}`}>
                  <div className="chat-sender-label">
                    {msg.sender === 'user' ? '👤 Operator' : '🤖 SentinelCore'}
                    {msg.agentUsed && (
                      <span className="agent-badge">{getAgentIcon(msg.agentUsed)} {msg.agentUsed}</span>
                    )}
                  </div>
                  <div className={`chat-bubble ${msg.sender}`}>
                    <div className="bubble-content">
                      {renderFormattedText(msg.text)}
                    </div>
                    {msg.attachmentsProcessed && msg.attachmentsProcessed > 0 && msg.sender === 'user' && (
                      <div className="attachment-indicator">
                        📎 {msg.attachmentsProcessed} file(s) attached
                      </div>
                    )}
                  </div>
                  {/* Metadata bar for sentinel messages */}
                  {msg.sender === 'sentinel' && msg.intent && (
                    <div className="message-metadata">
                      <span className={`severity-badge ${getSeverityClass(msg.severity)}`}>
                        {msg.severity}
                      </span>
                      <span className="meta-item" title="Intent">🎯 {msg.intent}</span>
                      <span className="meta-item" title="Confidence">📊 {((msg.confidence || 0) * 100).toFixed(0)}%</span>
                      <span className="meta-item" title="Threat Score">⚡ {((msg.threatScore || 0) * 100).toFixed(0)}%</span>
                      {msg.processingTime && (
                        <span className="meta-item" title="Processing Time">⏱️ {msg.processingTime}ms</span>
                      )}
                      {msg.xaiTrace && (
                        <button
                          className="xai-btn"
                          onClick={() => { setActiveXai(msg.xaiTrace); setShowXaiPanel(true); }}
                          title="View XAI Trace"
                        >
                          🔍 XAI
                        </button>
                      )}
                    </div>
                  )}
                  {/* Guardrail flags */}
                  {msg.guardrailFlags && msg.guardrailFlags.length > 0 && (
                    <div className="guardrail-flags">
                      {msg.guardrailFlags.map((flag: any, i: number) => (
                        <div key={i} className={`guardrail-flag ${flag.severity?.toLowerCase()}`}>
                          🛡️ {flag.type}: {flag.detail}
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="chat-timestamp">{msg.timestamp}</div>
                </div>
              ))}
              {isTyping && (
                <div className="chat-bubble-container sentinel">
                  <div className="chat-sender-label">🤖 SentinelCore</div>
                  <div className="chat-bubble sentinel typing-indicator">
                    <span className="typing-text">Investigating</span>
                    <span className="typing-dots">
                      <span /><span /><span />
                    </span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Attachment Preview */}
          {attachments.length > 0 && (
            <div className="attachment-preview-bar">
              {attachments.map((att, i) => (
                <div key={i} className="attachment-preview-item">
                  {att.preview ? (
                    <img src={att.preview} alt={att.file.name} className="attachment-thumb" />
                  ) : (
                    <span className="attachment-file-icon">{getFileIcon(att.type)}</span>
                  )}
                  <span className="attachment-name">{att.file.name}</span>
                  <button className="attachment-remove" onClick={() => removeAttachment(i)}>×</button>
                </div>
              ))}
            </div>
          )}

          {/* Input Area */}
          <div className="chat-input-area">
            <input
              type="file"
              ref={fileInputRef}
              multiple
              style={{ display: 'none' }}
              onChange={handleFileSelect}
              accept="image/*,audio/*,video/*,.exe,.dll,.bin,.apk,.pdf,.doc,.docx,.csv,.json,.log,.db,.sqlite"
            />
            <button
              className="attach-btn"
              onClick={() => fileInputRef.current?.click()}
              title="Attach file for multi-modal analysis"
            >
              📎
            </button>
            <input
              type="text"
              id="sentinel-input"
              placeholder="Investigate threats, analyze evidence, query intelligence..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              id="sentinel-send"
              onClick={handleSend}
              disabled={(!inputText.trim() && attachments.length === 0) || isTyping}
              className="send-btn"
            >
              <span className="send-icon">▶</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
