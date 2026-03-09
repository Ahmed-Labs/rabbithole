import { useCallback, useEffect, useRef, useState } from "react";
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
const POLL_INTERVAL_MS = 2500;
const UPDATED_FLASH_MS = 2000;

type TaskStatus = "idle" | "polling" | "done" | "failed";

export function FlowPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const paperId = searchParams.get("paperId") ?? "";
  const depth = Number(searchParams.get("depth") ?? DEFAULT_DEPTH);

  const [nodes, setNodes] = useState<PaperFlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);
  const selectedPaper = nodes.find((n) => n.id === selectedPaperId)?.data ?? null;
  const [taskStatus, setTaskStatus] = useState<TaskStatus>("idle");
  const [pendingCount, setPendingCount] = useState(0);
  const [rf, setRf] = useState<ReactFlowInstance<PaperFlowNode, Edge> | null>(null);

  const taskIdRef = useRef<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const onNodesChange: OnNodesChange<PaperFlowNode> = useCallback((changes) => {
    setNodes((curr) => applyNodeChanges(changes, curr));
  }, []);

  const onNodeClick: NodeMouseHandler<PaperFlowNode> = useCallback((_e, node) => {
    setSelectedPaperId(node.id);
  }, []);

  // Mark nodes that got new llm_explanation with isUpdated, then clear after flash
  function applyUpdatedFlash(
    prevNodes: PaperFlowNode[],
    nextNodes: PaperFlowNode[],
  ): PaperFlowNode[] {
    const prevById = new Map(prevNodes.map((n) => [n.id, n]));
    const withFlash = nextNodes.map((n) => {
      const prev = prevById.get(n.id);
      const justScored =
        prev?.data.llm_explanation == null && n.data.llm_explanation != null;
      return justScored ? { ...n, data: { ...n.data, isUpdated: true } } : n;
    });

    // Clear flash after animation completes
    setTimeout(() => {
      setNodes((curr) =>
        curr.map((n) =>
          n.data.isUpdated ? { ...n, data: { ...n.data, isUpdated: false } } : n,
        ),
      );
    }, UPDATED_FLASH_MS);

    return withFlash;
  }

  function centerOnRoot(flowNodes: PaperFlowNode[], instance: ReactFlowInstance<PaperFlowNode, Edge>) {
    const root = flowNodes.find((n) => n.data.isRoot);
    if (!root) return;
    const cx = root.position.x + NODE_W / 2;
    const cy = root.position.y + NODE_H / 2;
    requestAnimationFrame(() => {
      instance.setCenter(cx, cy, { zoom: INITIAL_ZOOM, duration: 0 });
    });
  }

  // Refetch after task completes, diff against current nodes to flash updated ones
  async function refetchAfterTask(signal: AbortSignal) {
    const qs = new URLSearchParams({ max_depth: String(depth) });
    const res = await fetch(
      `/api/graph/${encodeURIComponent(paperId)}?${qs}`,
      { headers: { Accept: "application/json" }, signal },
    );
    if (!res.ok) return;

    const { data }: GraphResponse = await res.json();
    const { nodes: freshNodes, edges: freshEdges } = toCompactFlowGraph(data);

    setNodes((prev) => applyUpdatedFlash(prev, freshNodes));
    setEdges(freshEdges);
    setTaskStatus("done");
    setPendingCount(0);
  }

  // Polling loop
  function schedulePoll(taskId: string, signal: AbortSignal) {
    if (signal.aborted) return;

    pollTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/task-status/${taskId}`, { signal });
        if (!res.ok) { setTaskStatus("failed"); return; }

        const json = await res.json();

        if (json.status === "SUCCESS") {
          await refetchAfterTask(signal);
        } else if (json.status === "FAILURE") {
          setTaskStatus("failed");
        } else {
          // PENDING or STARTED — keep polling
          schedulePoll(taskId, signal);
        }
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setTaskStatus("failed");
      }
    }, POLL_INTERVAL_MS);
  }

  // Main load effect
  useEffect(() => {
    if (!paperId) {
      setNodes([]); setEdges([]); setSelectedPaperId(null);
      return;
    }

    // Cancel previous request + polling
    abortRef.current?.abort();
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    const controller = new AbortController();
    abortRef.current = controller;

    setTaskStatus("idle");
    setPendingCount(0);

    async function load() {
      try {
        const qs = new URLSearchParams({ max_depth: String(depth) });
        const res = await fetch(
          `/api/graph/${encodeURIComponent(paperId)}?${qs}`,
          { headers: { Accept: "application/json" }, signal: controller.signal },
        );

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const { data, task_id }: GraphResponse = await res.json();
        const { nodes: flowNodes, edges: flowEdges } = toCompactFlowGraph(data);

        // Mark nodes without llm_explanation as pending if a task is running
        const pending = task_id
          ? flowNodes.map((n) =>
              n.data.llm_explanation == null
                ? { ...n, data: { ...n.data, isPending: true } }
                : n,
            )
          : flowNodes;

        const pendingN = pending.filter((n) => n.data.isPending).length;

        setNodes(pending);
        setEdges(flowEdges);
        setSelectedPaperId(null);
        setPendingCount(pendingN);

        if (rf) centerOnRoot(flowNodes, rf);

        if (task_id && pendingN > 0) {
          taskIdRef.current = task_id;
          setTaskStatus("polling");
          schedulePoll(task_id, controller.signal);
        }
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        console.error(e);
        setNodes([]); setEdges([]); setSelectedPaperId(null);
      }
    }

    load();

    return () => {
      controller.abort();
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
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

          {/* AI scoring status pill */}
          {taskStatus === "polling" && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 rounded-full bg-zinc-900/90 border border-violet-500/40 px-4 py-2 text-xs text-violet-300 shadow-lg backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-violet-400 animate-ping" />
              AI scoring {pendingCount} paper{pendingCount !== 1 ? "s" : ""}…
            </div>
          )}

          {taskStatus === "done" && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 rounded-full bg-zinc-900/90 border border-emerald-500/40 px-4 py-2 text-xs text-emerald-300 shadow-lg backdrop-blur-sm ai-done-pill">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              AI scoring complete
            </div>
          )}

          {selectedPaper && (
            <DetailPanel
              data={selectedPaper}
              onClose={() => setSelectedPaperId(null)}
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

  /* Shimmer border for nodes awaiting AI score */
  @keyframes pending-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
    50% { box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.35); }
  }
  .paper-node-pending {
    animation: float 3s ease-in-out infinite, pending-pulse 2s ease-in-out infinite;
  }

  /* Pop flash when AI score arrives */
  @keyframes score-pop {
    0%   { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); transform: scale(1); }
    30%  { box-shadow: 0 0 0 8px rgba(52, 211, 153, 0.5); transform: scale(1.04); }
    100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); transform: scale(1); }
  }
  .paper-node-updated {
    animation: score-pop ${UPDATED_FLASH_MS}ms ease-out forwards !important;
  }

  /* Fade out the done pill */
  @keyframes fade-out {
    0%   { opacity: 1; }
    60%  { opacity: 1; }
    100% { opacity: 0; }
  }
  .ai-done-pill {
    animation: fade-out 3s ease-out forwards;
  }
`;