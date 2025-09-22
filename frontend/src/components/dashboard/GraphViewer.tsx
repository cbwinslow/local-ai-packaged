'use client'

import React, { useState } from 'react';

interface GraphViewerProps {
  data: any;
}

export function GraphViewer({ data }: GraphViewerProps) {
  const [zoom, setZoom] = useState(1);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Placeholder for graph rendering library (e.g., vis-network or react-flow)
  return (
    <div className="graph-viewer">
      <div className="controls">
        <button onClick={() => setZoom(zoom + 0.1)}>Zoom In</button>
        <button onClick={() => setZoom(Math.max(0.1, zoom - 0.1))}>Zoom Out</button>
      </div>
      <div className="graph-container">
        <div className="node-list">
          {data.nodes?.map((node: any) => (
            <div key={node.id} onClick={() => setSelectedNode(node.id)}>
              {node.label}
            </div>
          ))}
        </div>
        <div className="relationships">
          {data.edges?.map((edge: any) => (
            <div key={edge.id}>
              {edge.from} -- {edge.to}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
