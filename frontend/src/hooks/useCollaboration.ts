// src/hooks/useCollaboration.ts
import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface PeerInfo {
  id: string;
  avatarUrl?: string;
}

interface ActionPayload {
  type: string;
  data: any;
}

// Hook for real‑time collaboration via Socket.io
export default function useCollaboration() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [peers, setPeers] = useState<PeerInfo[]>([]);

  useEffect(() => {
    const s = io(import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000');
    setSocket(s);
    // When connected, request a session ID (backend can assign)
    s.emit('collaboration:join');
    s.on('session:id', (id: string) => setSessionId(id));
    s.on('peers:update', (list: PeerInfo[]) => setPeers(list));
    return () => {
      s.disconnect();
    };
  }, []);

  const sendAction = (type: string, data: any) => {
    if (!socket) return;
    const payload: ActionPayload = { type, data: { ...data, sessionId } };
    socket.emit('collaboration:action', payload);
  };

  return { socket, sessionId, peers, sendAction };
}
