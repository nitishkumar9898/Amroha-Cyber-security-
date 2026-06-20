import React, { useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { io, Socket } from 'socket.io-client';
import MetaverseSceneContent from './MetaverseSceneContent'; // Placeholder for actual scene content

// Initialize socket connection (adjust URL as needed)
const socket: Socket = io(import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000');

const MetaverseScene: React.FC = () => {
  const sceneRef = useRef(null);

  useEffect(() => {
    // Example: listen for session updates
    socket.on('training:update', (data) => {
      console.log('Training update:', data);
      // TODO: integrate with scene state
    });
    return () => {
      socket.off('training:update');
      socket.disconnect();
    };
  }, []);

  return (
    <Canvas ref={sceneRef} shadows>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 10, 5]} intensity={1} castShadow />
      {/* Add your 3D scene content here */}
      <MetaverseSceneContent />
    </Canvas>
  );
};

export default MetaverseScene;
