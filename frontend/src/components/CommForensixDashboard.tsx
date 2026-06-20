import React, { useState } from 'react';
import './CommForensixDashboard.css';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

// Placeholder data types
interface Message {
  scan_id: string;
  message_hash: string;
  sender_id: string;
  receiver_id: string;
  timestamp: string;
  algorithm: string;
  key_size: number;
  is_quantum_safe: boolean;
}

interface Call {
  scan_id: string;
  call_id: string;
  caller_id: string;
  callee_id: string;
  start_time: string;
  end_time: string;
  codec: string;
  packet_count: number;
  is_encrypted: boolean;
}

export const CommForensixDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // In a real app, you'd gather form data and POST to /api/commforensix/messages & /calls
      // Here we just simulate a delay.
      await new Promise((res) => setTimeout(res, 800));
      // Mock data
      setMessages([
        {
          scan_id: 'scan123',
          message_hash: 'abc123def',
          sender_id: 'userA',
          receiver_id: 'userB',
          timestamp: new Date().toISOString(),
          algorithm: 'SignalProtocol',
          key_size: 256,
          is_quantum_safe: false,
        },
      ]);
      setCalls([
        {
          scan_id: 'scan123',
          call_id: 'call789',
          caller_id: 'userA',
          callee_id: 'userC',
          start_time: new Date().toISOString(),
          end_time: new Date().toISOString(),
          codec: 'OPUS',
          packet_count: 1200,
          is_encrypted: true,
        },
      ]);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const trafficChartData = {
    labels: messages.map((m) => m.timestamp),
    datasets: [
      {
        label: 'Message Size (bytes)',
        data: messages.map(() => 1024), // placeholder size
        borderColor: '#00ffff',
        backgroundColor: 'rgba(0,255,255,0.2)',
      },
    ],
  };

  return (
    <div className="commforensix-dashboard">
      <h2>CommForensix – Encrypted Communication Forensics</h2>
      <form onSubmit={handleUpload} className="upload-form">
        <button type="submit" disabled={loading}>
          {loading ? 'Processing…' : 'Upload Sample Data'}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      <section className="section">
        <h3>Message Metadata</h3>
        <pre>{JSON.stringify(messages, null, 2)}</pre>
      </section>
      <section className="section">
        <h3>VoIP Call Metadata</h3>
        <pre>{JSON.stringify(calls, null, 2)}</pre>
      </section>
      <section className="section">
        <h3>Traffic Pattern Chart</h3>
        <Line data={trafficChartData} />
      </section>
    </div>
  );
};
