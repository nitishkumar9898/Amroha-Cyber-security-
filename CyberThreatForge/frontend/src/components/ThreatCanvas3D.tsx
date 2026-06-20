/**
 * =============================================================================
 * ThreatCanvas3D — 3D/XR Visualization Component
 * =============================================================================
 *
 * Renders a real-time 3D threat landscape using Three.js.
 * Features:
 *   - Evidence graph (Neo4j) visualization in 3D space
 *   - APT attack chain animation
 *   - Geographic threat heatmap overlay
 *   - Time-travel slider (historical state replay)
 *   - VR mode for immersive investigation (WebXR)
 *
 * Integrates with SentinelCore for real-time data streaming.
 */

import { useEffect, useRef, useCallback } from 'react';

// Three.js types (would be imported in real build)
interface ThreeScene {
  scene: unknown;
  camera: unknown;
  renderer: unknown;
}

export interface GraphNode {
  id: string;
  type: 'evidence' | 'actor' | 'ioc' | 'case' | 'entity';
  label: string;
  properties: Record<string, unknown>;
  position: [number, number, number];
  riskScore: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
  properties: Record<string, unknown>;
}

export interface ThreatCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeSelect?: (node: GraphNode) => void;
  onEdgeSelect?: (edge: GraphEdge) => void;
  vrEnabled?: boolean;
  timeRange?: { start: string; end: string };
}

export function ThreatCanvas3D({
  nodes,
  edges,
  onNodeSelect,
  vrEnabled = false,
}: ThreatCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<ThreeScene | null>(null);
  const animationFrameRef = useRef<number>();

  const initScene = useCallback(() => {
    if (!containerRef.current) return;
    // In production: init Three.js scene, WebGL renderer, OrbitControls
    // For VR: init XR session via navigator.xr
    sceneRef.current = { scene: {}, camera: {}, renderer: {} };
  }, []);

  const buildGraph = useCallback(() => {
    if (!sceneRef.current) return;
    // For each node: create a sphere + label sprite
    // For each edge: create a cylinder/line between spheres
    // Color code by type and risk score
    // Animate with force-directed layout (d3-force or ngraph)
  }, [nodes, edges]);

  const animate = useCallback(() => {
    animationFrameRef.current = requestAnimationFrame(animate);
    if (!sceneRef.current) return;
    // Rotate, update positions, render
  }, []);

  useEffect(() => {
    initScene();
    buildGraph();
    animate();
    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [initScene, buildGraph, animate]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-gray-950 rounded-lg overflow-hidden"
      role="application"
      aria-label="3D Threat Intelligence Canvas"
    >
      {/* Control overlays */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button className="px-3 py-1 bg-gray-800/80 text-xs text-gray-300 rounded hover:bg-gray-700">
          Fit View
        </button>
        <button className="px-3 py-1 bg-gray-800/80 text-xs text-gray-300 rounded hover:bg-gray-700">
          Center
        </button>
        {vrEnabled && (
          <button className="px-3 py-1 bg-cyan-800/80 text-xs text-cyan-300 rounded hover:bg-cyan-700">
            Enter VR
          </button>
        )}
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-gray-900/80 p-3 rounded text-xs space-y-1">
        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500" /> APT Actor</div>
        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-amber-500" /> IOC</div>
        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-500" /> Evidence</div>
        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-green-500" /> Entity</div>
        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-purple-500" /> Case</div>
      </div>

      {/* Information panel */}
      <div className="absolute bottom-4 right-4 z-10 bg-gray-900/80 p-3 rounded text-xs text-gray-400">
        {nodes.length} nodes · {edges.length} edges
      </div>
    </div>
  );
}
