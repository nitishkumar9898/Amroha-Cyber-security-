import React, { useState } from 'react';
import './ResearchHub.css';

interface PaperResult {
  title: string;
  authors: string[];
  date: string;
  abstract: string;
  methodology: string;
  results: string;
  conclusion: string;
  patent_suggestion: string;
  cryptographic_hash: string;
}

export const ResearchHub: React.FC = () => {
  const [topic, setTopic] = useState('Quantum-Enabled Ransomware');
  const [datasetSize, setDatasetSize] = useState(15000);
  const [isGenerating, setIsGenerating] = useState(false);
  const [paper, setPaper] = useState<PaperResult | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch(`/api/research/generate?topic=${encodeURIComponent(topic)}&dataset_size=${datasetSize}`, {
        method: 'POST',
      });
      const data = await response.json();
      setPaper(data);
    } catch (error) {
      console.error("Failed to generate paper", error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="research-hub fade-in">
      <div className="research-header">
        <h2>📚 Auto-Research & Publications Lab</h2>
        <p>Utilize SentinelCore to autonomously synthesize aggregated threat intelligence into peer-review ready academic papers and patent drafts.</p>
      </div>

      <div className="research-controls glass-panel">
        <div className="form-group">
          <label>Research Topic Vector</label>
          <input 
            type="text" 
            value={topic} 
            onChange={(e) => setTopic(e.target.value)} 
          />
        </div>
        <div className="form-group">
          <label>Dataset Aggregation Size (N)</label>
          <input 
            type="number" 
            value={datasetSize} 
            onChange={(e) => setDatasetSize(parseInt(e.target.value))} 
            min="1000"
            max="1000000"
          />
        </div>
        <button 
          className="cyber-button primary" 
          onClick={handleGenerate} 
          disabled={isGenerating}
        >
          {isGenerating ? 'Synthesizing Data...' : 'Generate Academic Paper'}
        </button>
      </div>

      {paper && (
        <div className="paper-result glass-panel fade-in">
          <h1 className="paper-title">{paper.title}</h1>
          <div className="paper-meta">
            <span><strong>Authors:</strong> {paper.authors.join(', ')}</span>
            <span><strong>Date:</strong> {paper.date}</span>
            <span className="crypto-hash"><strong>Integrity Hash:</strong> {paper.cryptographic_hash.substring(0, 16)}...</span>
          </div>
          
          <div className="paper-section">
            <h3>Abstract</h3>
            <p>{paper.abstract}</p>
          </div>
          
          <div className="paper-section">
            <h3>Methodology & Compliance</h3>
            <p>{paper.methodology}</p>
          </div>
          
          <div className="paper-section">
            <h3>Key Results</h3>
            <p>{paper.results}</p>
          </div>
          
          <div className="paper-section">
            <h3>Conclusion</h3>
            <p>{paper.conclusion}</p>
          </div>
          
          <div className="patent-alert">
            <strong>💡 AI Patent Suggestion:</strong> {paper.patent_suggestion}
          </div>
        </div>
      )}
    </div>
  );
};
