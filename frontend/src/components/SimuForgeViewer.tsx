// frontend/src/components/SimuForgeViewer.tsx
import React, { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Minimal 3‑D viewer for SimuForge simulation runs.
 * It renders a simple network of spheres (nodes) and lines (edges).
 * The component expects a `history` prop – an array of snapshots
 * produced by the simulation engine (year, environment.nodes).
 */
interface NodeInfo {
  id: string;
  vulnerable?: boolean;
  compromised?: boolean;
}

interface Snapshot {
  year: number;
  environment: { nodes: NodeInfo[] };
}

interface Props {
  history: Snapshot[];
}

const SimuForgeViewer: React.FC<Props> = ({ history }) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const width = mountRef.current?.clientWidth || 800;
    const height = mountRef.current?.clientHeight || 600;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 30;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mountRef.current?.appendChild(renderer.domElement);

    // Light
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(0, 20, 10);
    scene.add(light);

    // Helper to create sphere mesh for a node
    const createNodeMesh = (node: NodeInfo) => {
      const color = node.compromised
        ? 0xff0000 // red for compromised
        : node.vulnerable
        ? 0xffa500 // orange for vulnerable
        : 0x00ff00; // green otherwise
      const geometry = new THREE.SphereGeometry(1, 16, 16);
      const material = new THREE.MeshStandardMaterial({ color });
      return new THREE.Mesh(geometry, material);
    };

    // Layout: place nodes in a circle
    const radius = 12;
    const nodeMeshes: { [id: string]: THREE.Mesh } = {};
    const nodeCount = history[0]?.environment.nodes.length || 0;
    history[0]?.environment.nodes.forEach((node, idx) => {
      const angle = (idx / nodeCount) * Math.PI * 2;
      const mesh = createNodeMesh(node);
      mesh.position.set(Math.cos(angle) * radius, Math.sin(angle) * radius, 0);
      scene.add(mesh);
      nodeMeshes[node.id] = mesh;
    });

    // Animate through years
    let currentIdx = 0;
    const animate = () => {
      requestAnimationFrame(animate);
      if (history[currentIdx]) {
        const snap = history[currentIdx];
        // Update node colors based on state at this tick
        snap.environment.nodes.forEach((node) => {
          const mesh = nodeMeshes[node.id];
          if (mesh) {
            const newColor = node.compromised
              ? 0xff0000
              : node.vulnerable
              ? 0xffa500
              : 0x00ff00;
            (mesh.material as THREE.MeshStandardMaterial).color.setHex(newColor);
          }
        });
        // Simple rotation for visual flair
        scene.rotation.y += 0.001;
        currentIdx = (currentIdx + 1) % history.length;
      }
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      // Cleanup on unmount
      renderer.dispose();
      if (mountRef.current?.contains(renderer.domElement)) {
        mountRef.current?.removeChild(renderer.domElement);
      }
    };
  }, [history]);

  return <div ref={mountRef} style={{ width: "100%", height: "100%" }} />;
};

export default SimuForgeViewer;
