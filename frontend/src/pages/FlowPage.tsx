import { useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ReactFlow,
  Background,
  MiniMap,
  applyNodeChanges,
} from "@xyflow/react";
import type {
  Edge,
  NodeTypes,
  NodeMouseHandler,
  OnNodesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import { MOCK_GRAPH } from "../../mocks/mockGraph";
import type { GraphData, PaperFlowNode, PaperNodeData } from "../types/graph";
import { PaperNode } from "../components/PaperNode";
import { relevanceColor } from "../utils/relevanceColor";
import { DetailPanel } from "../components/DetailPanel";
import { Legend } from "../components/Legend";
import { FlowControls } from "../components/FlowControls";
import { FlowHeader } from "../components/FlowHeader";

const nodeTypes: NodeTypes = { paperNode: PaperNode };

const NODE_W = 210;
const NODE_H = 100;

const floatStyle = `
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-4px); }
  }
  .paper-node-float {
    animation: float 3s ease-in-out infinite;
  }
`;

function toFlowGraph(schema: GraphData): {
  nodes: PaperFlowNode[];
  edges: Edge[];
} {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));

  schema.nodes.forEach((n) =>
    g.setNode(n.id, { width: NODE_W, height: NODE_H }),
  );
  schema.edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  const rootNode = g.node(schema.root_id);
  const offsetX = rootNode ? rootNode.x : 0;
  const offsetY = rootNode ? rootNode.y : 0;

  const nodes: PaperFlowNode[] = schema.nodes.map((n) => {
    const { x, y } = g.node(n.id);
    return {
      id: n.id,
      type: "paperNode",
      position: { x: x - offsetX, y: y - offsetY },
      data: {
        title: n.data.title,
        year: n.data.year,
        citation_count: n.data.citation_count,
        relevance_score: n.data.relevance_score,
        abstract: n.data.abstract,
        authors: n.data.authors,
        pdf_url: n.data.pdf_url,
        url: n.data.url,
        isRoot: n.data.is_root,
        llm_explanation: n.data.llm_explanation,
      },
    };
  });

  const edges: Edge[] = schema.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    animated: true,
    style: { stroke: "#3f3f46", strokeWidth: 1.5 },
  }));

  return { nodes, edges };
}

export function FlowPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const paperId = searchParams.get("paperId") ?? "";
  const depth = Number(searchParams.get("depth") ?? 3);

  const { nodes: initialNodes, edges } = toFlowGraph(MOCK_GRAPH.data);
  const [nodes, setNodes] = useState<PaperFlowNode[]>(initialNodes);
  const [selectedPaper, setSelectedPaper] = useState<PaperNodeData | null>(
    null,
  );

  const onNodesChange: OnNodesChange<PaperFlowNode> = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  );

  const onNodeClick: NodeMouseHandler = useCallback((_e, node) => {
    setSelectedPaper((node as unknown as PaperFlowNode).data);
  }, []);

  return (
    <>
      <style>{floatStyle}</style>
      <div className="h-screen flex flex-col bg-[var(--color-page-bg)] text-white">
        <FlowHeader onBack={() => navigate(-1)} />

        <div className="flex-1 min-h-0 m-6 rounded-lg overflow-hidden bg-[var(--color-input-bg-dark)] flex flex-col relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onNodeClick={onNodeClick}
            fitView
          >
            <Background color="var(--color-border-default)" gap={20} />
            <FlowControls />
            <Legend />
            <MiniMap
              className="!bg-[var(--color-panel-bg)] !border !border-zinc-700 rounded-lg"
              nodeColor={(node) => {
                const d = (node as unknown as PaperFlowNode).data;
                return d.isRoot ? "#818cf8" : relevanceColor(d.relevance_score);
              }}
              nodeStrokeWidth={0}
              maskColor="rgba(9,13,20,0.6)"
            />
          </ReactFlow>

          {selectedPaper && (
            <DetailPanel
              data={selectedPaper}
              onClose={() => setSelectedPaper(null)}
            />
          )}
        </div>
      </div>
    </>
  );
}
