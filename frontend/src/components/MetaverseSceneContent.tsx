import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import * as THREE from 'three';

const ThreatNodeMesh: React.FC<{ position: [number, number, number]; color: string }> = ({ position, color }) => {
  const meshRef = useRef<THREE.Mesh>(null!);

  useFrame((_state, delta) => {
    meshRef.current.rotation.x += delta * 0.3;
    meshRef.current.rotation.y += delta * 0.4;
  });

  return (
    <mesh position={position} ref={meshRef}>
      <icosahedronGeometry args={[0.5, 1]} />
      <meshStandardMaterial color={color} wireframe={true} />
    </mesh>
  );
};

const MetaverseSceneContent: React.FC = () => {
  return (
    <>
      <OrbitControls enableDamping />
      <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade />
      <ThreatNodeMesh position={[0, 0, 0]} color="#ff003c" />
      <ThreatNodeMesh position={[3, 2, -2]} color="#f5b142" />
      <ThreatNodeMesh position={[-4, 1, 1]} color="#f5b142" />
      <ThreatNodeMesh position={[1, -3, 2]} color="#b142f5" />
    </>
  );
};

export default MetaverseSceneContent;
