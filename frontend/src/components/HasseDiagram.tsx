import React, { useCallback } from 'react';
import ReactFlow, {
  useNodesState,
  useEdgesState,
  Position,
  type Node,
  type Edge,
} from 'reactflow';
import dagre from 'dagre'; // Try default import again, it is standard for dagre in TS
import 'reactflow/dist/style.css';

interface HasseDiagramProps {
  apiBase: string;
  onNodeClick?: (nodeId: string) => void;
}

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: 'BT' }); // Bottom-to-Top (Parts -> Assembly)

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = Position.Bottom;
    node.sourcePosition = Position.Top; // Arrows go UP

    // We make sure to check nodeWithPosition exists
    if (nodeWithPosition) {
      node.position = {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      };
    }
  });

  return { nodes, edges };
};

export function HasseDiagram({ apiBase, onNodeClick }: HasseDiagramProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Fetch data
  React.useEffect(() => {
    fetch(`${apiBase}/api/hasse`)
      .then(res => res.json())
      .then(data => {
        // Layout the graph
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
          data.nodes || [],
          data.edges || []
        );
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
      })
      .catch(err => console.error("Failed to load Hasse data", err));
  }, [apiBase, setNodes, setEdges]);

  const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (onNodeClick) {
      onNodeClick(node.id);
    }
  }, [onNodeClick]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
      />
    </div>
  );
}
