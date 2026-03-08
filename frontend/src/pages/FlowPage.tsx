import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ReactFlow,
  Background,
  MiniMap,
  applyNodeChanges,
} from "@xyflow/react";
import type {
  Edge,
  NodeMouseHandler,
  OnNodesChange,
  ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type {
  GraphResponse,
  PaperFlowNode,
  PaperNodeData,
} from "../types/graph";
import { relevanceColor } from "../utils/relevanceColor";
import { DetailPanel } from "../components/DetailPanel";
import { Legend } from "../components/Legend";
import { FlowControls } from "../components/FlowControls";
import { nodeTypes, toCompactFlowGraph } from "../utils/graph";
import { AppHeader } from "../components/AppHeader";

const NODE_W = 210;
const NODE_H = 100;
const INITIAL_ZOOM = 0.8;
const DEFAULT_DEPTH = 3;

export function FlowPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const paperId = searchParams.get("paperId") ?? "";
  const depth = Number(searchParams.get("depth") ?? DEFAULT_DEPTH);

  const [nodes, setNodes] = useState<PaperFlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<PaperNodeData | null>(
    null,
  );
  const [rf, setRf] = useState<ReactFlowInstance<PaperFlowNode, Edge> | null>(
    null,
  );

  const onNodesChange: OnNodesChange<PaperFlowNode> = useCallback((changes) => {
    setNodes((curr) => applyNodeChanges(changes, curr));
  }, []);

  const onNodeClick: NodeMouseHandler<PaperFlowNode> = useCallback(
    (_e, node) => {
      setSelectedPaper(node.data);
    },
    [],
  );

  useEffect(() => {
    if (!paperId) {
      setNodes([]);
      setEdges([]);
      setSelectedPaper(null);
      return;
    }

    const controller = new AbortController();

    async function load() {
      try {
        const qs = new URLSearchParams({
          max_depth: String(depth),
        });

        const url = `/api/graph/${encodeURIComponent(paperId)}?${qs.toString()}`;

        const res = await fetch(url, {
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`Failed to fetch graph: ${res.status}`);
        }

        const { data }: GraphResponse = await res.json();
        const { nodes: flowNodes, edges: flowEdges } = toCompactFlowGraph(data);

        setNodes(flowNodes);
        setEdges(flowEdges);
        setSelectedPaper(null);

        const root = flowNodes.find((node) => node.data.isRoot);
        if (rf && root) {
          const centerX = root.position.x + NODE_W / 2;
          const centerY = root.position.y + NODE_H / 2;

          requestAnimationFrame(() => {
            rf.setCenter(centerX, centerY, {
              zoom: INITIAL_ZOOM,
              duration: 0,
            });
          });
        }
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        console.error(e);
        setNodes([]);
        setEdges([]);
        setSelectedPaper(null);
      }
    }

    load();

    return () => controller.abort();
  }, [paperId, depth, rf]);

  return (
    <>
      <style>{floatStyle}</style>

      <div className="h-screen flex flex-col bg-page-bg text-white">
        <AppHeader showBack onBack={() => navigate(-1)} />

        <div className="relative m-6 flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg bg-input-bg-dark">
          <ReactFlow<PaperFlowNode, Edge>
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onNodeClick={onNodeClick}
            onInit={setRf}
            autoPanOnNodeFocus={false}
          >
            <Background color="var(--color-border-default)" gap={20} />
            <FlowControls />
            <Legend />
            <MiniMap
              className="bg-panel-bg! border! border-zinc-700! rounded-lg"
              nodeColor={getNodeColor}
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

function getNodeColor(node: { data?: unknown }) {
  const data = node.data as PaperNodeData | undefined;
  if (!data) return "#71717a";
  return data.isRoot ? "#818cf8" : relevanceColor(data.relevance_score);
}

const floatStyle = `
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-4px); }
  }

  .paper-node-float {
    animation: float 3s ease-in-out infinite;
  }
`;
