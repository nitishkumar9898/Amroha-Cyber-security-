import { useEffect, useRef } from 'react';
import { Network } from 'vis-network';

interface NetworkNode {
  id: string;
  label: string;
  type: string;
}

interface NetworkLink {
  source: string;
  target: string;
  relationship: string;
}

interface NetworkChartProps {
  graphData?: {
    actor: string;
    nodes: NetworkNode[];
    links: NetworkLink[];
  };
}

export const NetworkChart = ({ graphData }: NetworkChartProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Use passed data or default mock data
    const nodesData = graphData?.nodes || [
      { id: 'Actor', label: 'APT-Shadow-Agent-01', type: 'actor' },
      { id: 'IP_1', label: '194.26.29.80', type: 'infrastructure' },
      { id: 'Wallet_1', label: 'bc1qxy2kg3ut7wvuf5vavfecsl7t6sn20agwxadg3d', type: 'wallet' },
      { id: 'Server_1', label: 'gov_research_server', type: 'target' }
    ];

    const linksData = graphData?.links || [
      { source: 'Actor', target: 'IP_1', relationship: 'USES_IP' },
      { source: 'Actor', target: 'Wallet_1', relationship: 'RECEIVES_FUNDS' },
      { source: 'IP_1', target: 'Server_1', relationship: 'ATTACKED' }
    ];

    // Map to vis-network format
    const visNodes = nodesData.map(node => {
      let color = '#38bdf8'; // Default cyan
      if (node.type === 'actor') color = '#ec4899'; // pink
      else if (node.type === 'infrastructure') color = '#8b5cf6'; // purple
      else if (node.type === 'wallet') color = '#f59e0b'; // amber
      else if (node.type === 'target') color = '#ef4444'; // red

      return {
        id: node.id,
        label: node.label,
        color: {
          background: '#0a0e17',
          border: color,
          highlight: {
            background: color,
            border: '#ffffff'
          }
        },
        title: `Type: ${node.type.toUpperCase()}`
      };
    });

    const visEdges = linksData.map(link => ({
      from: link.source,
      to: link.target,
      label: link.relationship,
      font: {
        size: 9,
        color: '#64748b',
        face: 'JetBrains Mono',
        strokeWidth: 0
      }
    }));

    const network = new Network(
      containerRef.current,
      { nodes: visNodes, edges: visEdges },
      {
        nodes: {
          shape: 'dot',
          size: 16,
          borderWidth: 2,
          font: {
            size: 11,
            color: '#f1f5f9',
            face: 'Inter'
          },
          shadow: {
            enabled: true,
            color: 'rgba(6, 182, 212, 0.15)',
            size: 10,
            x: 0,
            y: 0
          }
        },
        edges: {
          width: 1.5,
          color: {
            color: 'rgba(56, 189, 248, 0.25)',
            highlight: '#38bdf8',
            hover: '#38bdf8'
          },
          arrows: {
            to: {
              enabled: true,
              scaleFactor: 0.5
            }
          },
          smooth: {
            enabled: true,
            type: 'continuous',
            roundness: 0.5
          }
        },
        interaction: {
          hover: true,
          tooltipDelay: 200,
          zoomView: true
        },
        physics: {
          enabled: true,
          solver: 'forceAtlas2Based',
          forceAtlas2Based: {
            gravitationalConstant: -50,
            centralGravity: 0.01,
            springLength: 100,
            springConstant: 0.08
          }
        }
      }
    );

    return () => {
      network.destroy();
    };
  }, [graphData]);

  return (
    <div 
      ref={containerRef} 
      style={{ 
        height: '280px', 
        width: '100%', 
        background: 'rgba(10, 14, 23, 0.2)',
        borderRadius: '8px'
      }} 
    />
  );
};
