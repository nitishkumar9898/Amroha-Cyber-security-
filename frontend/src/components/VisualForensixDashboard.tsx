import React, { useState } from 'react';
import './Dashboard.css';

const VisualForensixDashboard: React.FC = () => {
    const [mediaType, setMediaType] = useState<'image' | 'video'>('image');
    const [status, setStatus] = useState<string>('');
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [reportData, setReportData] = useState<any>(null);

    const runAnalysis = async () => {
        setStatus('Ingesting media...');
        setAnalysisResult(null);
        setReportData(null);

        // 1. Ingest
        const ingestRes = await fetch('/api/visualforensix/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                asset_id: `MEDIA-${Math.floor(Math.random() * 10000)}`,
                filename: mediaType === 'image' ? 'evidence_photo.jpg' : 'surveillance_clip.mp4',
                media_type: mediaType,
                file_size_kb: Math.random() * 5000 + 500
            })
        });
        const ingestData = await ingestRes.json();
        
        setStatus('Analyzing media for tampering/deepfakes...');

        // 2. Analyze
        const analyzeRes = await fetch('/api/visualforensix/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                asset_id: ingestData.asset_id,
                media_type: mediaType
            })
        });
        const analyzeData = await analyzeRes.json();
        setAnalysisResult(analyzeData);

        setStatus('Generating forensic report...');

        // 3. Generate Report
        const reportRes = await fetch('/api/visualforensix/generate-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                asset_id: analyzeData.asset_id,
                pixel_analysis: analyzeData.pixel_analysis,
                video_analysis: analyzeData.video_analysis
            })
        });
        const report = await reportRes.json();
        setReportData(report);
        setStatus('Analysis Complete.');
    };

    return (
        <div className="dashboard-container">
            <h2>VisualForensix Engine</h2>
            <p className="subtitle">High-precision image and video tampering detection.</p>
            
            <div className="control-panel">
                <div className="form-group">
                    <label>Media Type:</label>
                    <select value={mediaType} onChange={(e) => setMediaType(e.target.value as 'image' | 'video')}>
                        <option value="image">Image (Pixel Forgery / ELA)</option>
                        <option value="video">Video (Deepfake Temporal Analysis)</option>
                    </select>
                </div>
                <button onClick={runAnalysis} className="action-button">Run Forensic Analysis</button>
            </div>

            {status && <div className="status-indicator">Status: {status}</div>}

            {analysisResult && (
                <div className="results-panel">
                    <h3>Analysis Results</h3>
                    <div className="metric-grid">
                        <div className="metric-card">
                            <h4>Metadata Anomalies</h4>
                            <div className="metric-value warning">{analysisResult.metadata_anomalies} detected</div>
                        </div>

                        {mediaType === 'image' && analysisResult.pixel_analysis && (
                            <>
                                <div className="metric-card">
                                    <h4>ELA Tampering Score</h4>
                                    <div className={`metric-value ${analysisResult.pixel_analysis.is_tampered ? 'critical' : 'safe'}`}>
                                        {analysisResult.pixel_analysis.ela_score.toFixed(2)}%
                                    </div>
                                </div>
                                <div className="metric-card">
                                    <h4>Double Compression</h4>
                                    <div className="metric-value">
                                        {analysisResult.pixel_analysis.double_compression_detected ? "DETECTED" : "CLEAR"}
                                    </div>
                                </div>
                            </>
                        )}

                        {mediaType === 'video' && analysisResult.video_analysis && (
                            <>
                                <div className="metric-card">
                                    <h4>Temporal Inconsistency</h4>
                                    <div className={`metric-value ${analysisResult.video_analysis.is_deepfake ? 'critical' : 'safe'}`}>
                                        {analysisResult.video_analysis.temporal_inconsistency.toFixed(2)}%
                                    </div>
                                </div>
                                <div className="metric-card">
                                    <h4>Face Warp Artifacts</h4>
                                    <div className={`metric-value ${analysisResult.video_analysis.is_deepfake ? 'critical' : 'safe'}`}>
                                        {analysisResult.video_analysis.face_warp_artifacts.toFixed(2)}%
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {reportData && (
                <div className="results-panel summary-panel">
                    <h3>Court-Admissible Report Generated</h3>
                    <p><strong>Hash:</strong> {reportData.report_hash}</p>
                    <p><strong>Admissibility Score:</strong> {reportData.admissibility_score.toFixed(2)}%</p>
                    <p><strong>Conclusion:</strong> <span className={reportData.report_data.forensic_conclusion === 'TAMPERED' ? 'critical-text' : 'safe-text'}>{reportData.report_data.forensic_conclusion}</span></p>
                    <pre className="json-dump">{JSON.stringify(reportData.report_data, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default VisualForensixDashboard;
