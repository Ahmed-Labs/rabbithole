import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import {
  FilterSidebar,
  type FlowFilters,
} from "../components/FilterSidebar";

const NODE_W = 210;
const NODE_H = 100;
const INITIAL_ZOOM = 0.8;
const DEFAULT_DEPTH = 3;
const POLL_INTERVAL_MS = 2500;
const UPDATED_FLASH_MS = 2000;

const DEFAULT_FLOW_FILTERS: FlowFilters = {
  searchQuery: "",
  searchEnabled: true,
  yearMin: 1900,
  yearMax: new Date().getFullYear(),
  yearEnabled: false,
  minCitations: 0,
  citationsEnabled: false,
  minRelevance: 0,
  similarityEnabled: false,
};

type TaskStatus = "idle" | "polling" | "done" | "failed";

function buildGraphQueryString(
  depth: number,
  filters: FlowFilters,
): URLSearchParams {
  const qs = new URLSearchParams({ max_depth: String(depth) });
  if (filters.yearEnabled && filters.yearMin != null)
    qs.set("min_year", String(filters.yearMin));
  if (filters.yearEnabled && filters.yearMax != null)
    qs.set("max_year", String(filters.yearMax));
  if (filters.citationsEnabled && filters.minCitations != null)
    qs.set("min_citations", String(filters.minCitations));
  if (filters.similarityEnabled && filters.minRelevance != null)
    qs.set("min_relevance", String(filters.minRelevance));
  return qs;
}

function filterVisibleBySearch(
  nodes: PaperFlowNode[],
  edges: Edge[],
  searchQuery: string,
  searchEnabled: boolean,
): {
  displayNodes: PaperFlowNode[];
  displayEdges: Edge[];
} {
  if (!searchEnabled) {
    const nodeIds = new Set(nodes.map((n) => n.id));
    const displayEdges = edges.filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target),
    );
    return { displayNodes: nodes, displayEdges };
  }
  const q = searchQuery.trim().toLowerCase();
  if (!q) {
    const nodeIds = new Set(nodes.map((n) => n.id));
    const displayEdges = edges.filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target),
    );
    return { displayNodes: nodes, displayEdges };
  }
  const nodeIds = new Set(nodes.map((n) => n.id));
  const visibleIds = new Set(
    nodes
      .filter((n) => {
        const titleMatch = n.data.title?.toLowerCase().includes(q);
        const authorMatch = n.data.authors?.some((a) =>
          a.name?.toLowerCase().includes(q),
        );
        return titleMatch || authorMatch;
      })
      .map((n) => n.id),
  );
  // Filtered papers only visible when on a path from an unfiltered paper *toward the root*.
  const rootId = nodes.find((n) => n.data?.isRoot === true)?.id ?? null;
  const adj = new Map<string, Set<string>>();
  for (const e of edges) {
    if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) continue;
    if (!adj.has(e.source)) adj.set(e.source, new Set());
    adj.get(e.source)!.add(e.target);
    if (!adj.has(e.target)) adj.set(e.target, new Set());
    adj.get(e.target)!.add(e.source);
  }
  const distFromRoot = new Map<string, number>();
  if (rootId != null) {
    let frontier = new Set<string>([rootId]);
    let d = 0;
    while (frontier.size > 0) {
      for (const id of frontier) distFromRoot.set(id, d);
      const next = new Set<string>();
      for (const id of frontier) {
        for (const neighbor of adj.get(id) ?? []) {
          if (!distFromRoot.has(neighbor)) next.add(neighbor);
        }
      }
      frontier = next;
      d++;
    }
  }
  const displayIds = new Set(visibleIds);
  let frontier = new Set(visibleIds);
  while (frontier.size > 0) {
    const next = new Set<string>();
    for (const id of frontier) {
      const myD = distFromRoot.get(id) ?? Infinity;
      for (const neighbor of adj.get(id) ?? []) {
        if (displayIds.has(neighbor)) continue;
        const neighborD = distFromRoot.get(neighbor) ?? Infinity;
        if (neighborD < myD) {
          displayIds.add(neighbor);
          next.add(neighbor);
        }
      }
    }
    frontier = next;
  }
  const ghostIds = new Set<string>();
  for (const id of displayIds) {
    if (!visibleIds.has(id)) ghostIds.add(id);
  }
  const displayNodes = nodes
    .filter((n) => displayIds.has(n.id))
    .map((n) => {
      const isGhost =
        ghostIds.has(n.id) || (n.data as { isGhost?: boolean }).isGhost === true;
      return isGhost ? { ...n, data: { ...n.data, isGhost: true } } : n;
    });
  const displayEdges = edges.filter(
    (e) => displayIds.has(e.source) && displayIds.has(e.target),
  );
  return { displayNodes, displayEdges };
}

export function FlowPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const paperId = searchParams.get("paperId") ?? "";
  const depth = Number(searchParams.get("depth") ?? DEFAULT_DEPTH);

  const [nodes, setNodes] = useState<PaperFlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);
  const [filters, setFilters] = useState<FlowFilters>(DEFAULT_FLOW_FILTERS);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [taskStatus, setTaskStatus] = useState<TaskStatus>("idle");
  const [pendingCount, setPendingCount] = useState(0);
  const [rf, setRf] = useState<ReactFlowInstance<PaperFlowNode, Edge> | null>(
    null,
  );

  const { displayNodes, displayEdges } = useMemo(
    () =>
      filterVisibleBySearch(
        nodes,
        edges,
        filters.searchQuery,
        filters.searchEnabled,
      ),
    [nodes, edges, filters.searchQuery, filters.searchEnabled],
  );

  const selectedNode = displayNodes.find((n) => n.id === selectedPaperId);
  const selectedPaper = selectedNode?.data ?? null;
  const isSelectedGhost = selectedNode?.data?.isGhost === true;

  // Clear selection when selected node is no longer in the displayed graph
  useEffect(() => {
    if (!selectedPaperId) return;
    const stillDisplayed = displayNodes.some((n) => n.id === selectedPaperId);
    if (!stillDisplayed) setSelectedPaperId(null);
  }, [displayNodes, selectedPaperId]);

  const taskIdRef = useRef<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const onNodesChange: OnNodesChange<PaperFlowNode> = useCallback((changes) => {
    setNodes((curr) => applyNodeChanges(changes, curr));
  }, []);

  const onNodeClick: NodeMouseHandler<PaperFlowNode> = useCallback(
    (_e, node) => {
      setSelectedPaperId(node.id);
    },
    [],
  );

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
          n.data.isUpdated
            ? { ...n, data: { ...n.data, isUpdated: false } }
            : n,
        ),
      );
    }, UPDATED_FLASH_MS);

    return withFlash;
  }

  function centerOnRoot(
    flowNodes: PaperFlowNode[],
    instance: ReactFlowInstance<PaperFlowNode, Edge>,
  ) {
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
    const qs = buildGraphQueryString(depth, filtersRef.current);
    const res = await fetch(`/api/graph/${encodeURIComponent(paperId)}?${qs}`, {
      headers: { Accept: "application/json" },
      signal,
    });
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
        if (!res.ok) {
          setTaskStatus("failed");
          return;
        }

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
      setNodes([]);
      setEdges([]);
      setSelectedPaperId(null);
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
        const qs = buildGraphQueryString(depth, filters);
        const res = await fetch(
          `/api/graph/${encodeURIComponent(paperId)}?${qs}`,
          {
            headers: { Accept: "application/json" },
            signal: controller.signal,
          },
        );

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const { data, task_id }: GraphResponse = await res.json();
        const { nodes: flowNodes, edges: flowEdges } = toCompactFlowGraph(data);

        // Mark nodes without llm_explanation as pending if a task is running
        const pending = task_id
          ? flowNodes.map((n) =>
              !n.data.isRoot && n.data.llm_explanation == null
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
        setNodes([]);
        setEdges([]);
        setSelectedPaperId(null);
      }
    }

    load();

    return () => {
      controller.abort();
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [paperId, depth, filters.yearMin, filters.yearMax, filters.yearEnabled, filters.minCitations, filters.citationsEnabled, filters.minRelevance, filters.similarityEnabled, rf]);

  return (
    <>
      <style>{floatStyle}</style>

      <div className="h-screen flex flex-col bg-page-bg text-white">
        <AppHeader
          showBack
          onBack={() => navigate(-1)}
          showSearch
          searchValue={filters.searchQuery}
          onSearchChange={(v) =>
            setFilters((f) => ({ ...f, searchQuery: v }))
          }
          onSearchSubmit={() => {}}
          searchPlaceholder="Search in graph…"
        />

        <div className="m-4 flex min-h-0 flex-1 gap-3">
          {/* Filter sidebar (collapsible) */}
          <div
            className="flex shrink-0 flex-col transition-[width] duration-200 ease-out overflow-hidden"
            style={{ width: sidebarOpen ? 240 : 0 }}
          >
            {sidebarOpen ? (
              <div className="w-[240px] h-full min-h-0">
                <FilterSidebar
                  filters={filters}
                  onFiltersChange={setFilters}
                  onReset={() => setFilters(DEFAULT_FLOW_FILTERS)}
                />
              </div>
            ) : null}
          </div>

          {/* Toggle filter sidebar */}
          <button
            type="button"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label={sidebarOpen ? "Close filters" : "Open filters"}
            aria-expanded={sidebarOpen}
            title={sidebarOpen ? "Close filters" : "Open filters"}
            className="
              shrink-0 self-center w-8 h-8 rounded-lg
              flex items-center justify-center
              bg-panel-bg border border-border-default
              text-text-muted hover:text-text hover:border-border-accent
              transition focus-visible:ring-2 focus-visible:ring-focus/40
            "
          >
            {sidebarOpen ? (
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                />
              </svg>
            ) : (
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 5l7 7-7 7M5 5l7 7-7 7"
                />
              </svg>
            )}
          </button>

          <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg bg-input-bg-dark">
          <ReactFlow<PaperFlowNode, Edge>
            nodes={displayNodes}
            edges={displayEdges}
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
              isFilteredOut={isSelectedGhost}
            />
          )}
          </div>
        </div>
      </div>
    </>
  );
}

function getNodeColor(node: { data?: unknown }) {
  const data = node.data as PaperNodeData | undefined;
  if (!data) return "#71717a";
  if (data.isGhost) return "#71717a";
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
