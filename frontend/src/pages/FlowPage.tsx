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
import { MOCK_GRAPH } from "../../mocks/mockGraph";
import type { GraphData, PaperFlowNode, PaperNodeData } from "../types/graph";
import { PaperNode } from "../components/PaperNode";
import { relevanceColor } from "../utils/relevanceColor";
import { DetailPanel } from "../components/DetailPanel";
import { Legend } from "../components/Legend";
import { FlowControls } from "../components/FlowControls";
import { FlowHeader } from "../components/FlowHeader";

const nodeTypes: NodeTypes = { paperNode: PaperNode };

const floatStyle = `
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-4px); }
  }
  .paper-node-float {
    animation: float 3s ease-in-out infinite;
  }
`;

function computePositions(
  schema: GraphData,
): Record<string, { x: number; y: number }> {
  const NODE_W = 260;
  const NODE_H = 200;
  const { root_id, edges } = schema;

  const children: Record<string, string[]> = {};
  const parents: Record<string, string[]> = {};
  schema.nodes.forEach((n) => {
    children[n.id] = [];
    parents[n.id] = [];
  });
  edges.forEach((e) => {
    children[e.source].push(e.target);
    parents[e.target].push(e.source);
  });

  const depth: Record<string, number> = {};
  const queue: string[] = [root_id];
  depth[root_id] = 0;
  while (queue.length) {
    const id = queue.shift()!;
    for (const child of children[id]) {
      if (depth[child] === undefined) {
        depth[child] = depth[id] + 1;
        queue.push(child);
      }
    }
  }

  const upQueue: string[] = [root_id];
  while (upQueue.length) {
    const id = upQueue.shift()!;
    for (const parent of parents[id]) {
      if (depth[parent] === undefined) {
        depth[parent] = depth[id] - 1;
        upQueue.push(parent);
      }
    }
  }

  schema.nodes.forEach((n) => {
    if (depth[n.id] === undefined) depth[n.id] = 0;
  });

  const levels: Record<number, string[]> = {};
  schema.nodes.forEach((n) => {
    const d = depth[n.id];
    if (!levels[d]) levels[d] = [];
    levels[d].push(n.id);
  });

  const positions: Record<string, { x: number; y: number }> = {};
  Object.entries(levels).forEach(([d, ids]) => {
    const totalWidth = (ids.length - 1) * NODE_W;
    ids.forEach((id, i) => {
      positions[id] = { x: i * NODE_W - totalWidth / 2, y: Number(d) * NODE_H };
    });
  });

  return positions;
}

function toFlowGraph(schema: GraphData): {
  nodes: PaperFlowNode[];
  edges: Edge[];
} {
  const positions = computePositions(schema);

  const nodes: PaperFlowNode[] = schema.nodes.map((n) => ({
    id: n.id,
    type: "paperNode",
    position: positions[n.id] ?? { x: 0, y: 0 },
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
  }));

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
