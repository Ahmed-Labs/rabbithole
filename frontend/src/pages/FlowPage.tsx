import { memo, useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  MiniMap,
  Panel,
  useReactFlow,
  Handle,
  Position,
  applyNodeChanges,
} from "@xyflow/react";
import type {
  Node,
  Edge,
  NodeTypes,
  NodeMouseHandler,
  OnNodesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import rabbitLogo from "../assets/rabbit-logo.png";
import { MOCK_GRAPH } from "../../mocks/mockGraph";

interface FlowPageProps {
  onBack: () => void;
}

interface PaperData {
  id: string;
  title: string;
  abstract: string;
  authors: { authorId: string; name: string }[];
  year: number;
  citation_count: number;
  relevance_score: number;
  is_root: boolean;
  pdf_url: string;
  url: string;
  llm_explanation: string | null;
}

interface SchemaNode {
  id: string;
  type: "paperNode";
  position: { x: number; y: number };
  data: PaperData;
}

interface SchemaEdge {
  id: string;
  source: string;
  target: string;
  type: "citationEdge";
  data: object;
}

interface GraphData {
  nodes: SchemaNode[];
  edges: SchemaEdge[];
  root_id: string;
}

export interface GraphSchema {
  data: GraphData;
}

function relevanceColor(score: number): string {
  if (score >= 0.8) return "#10b981";
  if (score >= 0.7) return "#84cc16";
  if (score >= 0.6) return "#eab308";
  if (score >= 0.5) return "#f59e0b";
  if (score >= 0.4) return "#f97316";
  if (score >= 0.3) return "#ef4444";
  return "#dc2626";
}

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
  const visited = new Set([root_id]);
  while (upQueue.length) {
    const id = upQueue.shift()!;
    for (const parent of parents[id]) {
      if (depth[parent] === undefined) {
        depth[parent] = depth[id] - 1;
        upQueue.push(parent);
        visited.add(parent);
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
      positions[id] = {
        x: i * NODE_W - totalWidth / 2,
        y: Number(d) * NODE_H,
      };
    });
  });

  return positions;
}

function toFlowGraph(schema: GraphData): { nodes: Node[]; edges: Edge[] } {
  const positions = computePositions(schema);

  const nodes: Node[] = schema.nodes.map((n) => ({
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

interface PaperNodeData {
  title: string;
  year: number;
  citation_count: number;
  relevance_score: number;
  abstract: string;
  authors: { authorId: string; name: string }[];
  pdf_url: string;
  url: string;
  isRoot: boolean;
  llm_explanation: string | null;
}

const PaperNode = memo(({ data }: { data: PaperNodeData }) => {
  const color = data.isRoot ? "#818cf8" : relevanceColor(data.relevance_score);
  const floatDelay = `${(data.title.length % 20) * 0.1}s`;
  return (
    <div
      className="rounded-lg bg-[var(--color-card-bg)] text-white text-xs w-52 cursor-pointer paper-node-float"
      style={{ border: `2px solid ${color}`, animationDelay: floatDelay }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: color, border: "none" }}
      />
      <div className="h-1 rounded-t-md" style={{ background: color }} />

      <div className="p-3 flex flex-col gap-1">
        <p className="font-semibold leading-snug line-clamp-3 text-[11px]">
          {data.title}
        </p>
        <div className="flex items-center justify-between mt-1">
          <span className="text-zinc-400 text-[10px]">{data.year}</span>
          {!data.isRoot && (
            <span
              className="text-[10px] font-medium px-1.5 py-0.5 rounded"
              style={{ background: color + "22", color }}
            >
              {(data.relevance_score * 100).toFixed(0)}%
            </span>
          )}
          {data.isRoot && (
            <span className="text-[10px] font-semibold text-indigo-300 px-1.5 py-0.5 rounded bg-indigo-900/40">
              Root
            </span>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: color, border: "none" }}
      />
    </div>
  );
});

const nodeTypes: NodeTypes = { paperNode: PaperNode };

function DetailPanel({
  data,
  onClose,
}: {
  data: PaperNodeData;
  onClose: () => void;
}) {
  const color = data.isRoot ? "#818cf8" : relevanceColor(data.relevance_score);
  return (
    <div className="absolute top-0 right-0 h-full w-80 bg-[var(--color-panel-bg)] border-l border-zinc-700 flex flex-col z-10 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-700">
        <span className="text-sm font-semibold text-white">Paper details</span>
        <button
          onClick={onClose}
          className="text-zinc-400 hover:text-white transition-colors text-lg leading-none"
        >
          ×
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        <div>
          <h3 className="text-sm font-semibold text-white leading-snug mb-2">
            {data.title}
          </h3>
          <div className="flex flex-wrap gap-2">
            <span className="text-[11px] text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">
              {data.year}
            </span>
            <span className="text-[11px] text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">
              {data.citation_count} citations
            </span>
            {!data.isRoot && (
              <span
                className="text-[11px] font-semibold px-2 py-0.5 rounded"
                style={{ background: color + "22", color }}
              >
                {(data.relevance_score * 100).toFixed(0)}% relevant
              </span>
            )}
          </div>
        </div>
        {data.authors.length > 0 && (
          <div>
            <p className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1">
              Authors
            </p>
            <p className="text-xs text-zinc-300">
              {data.authors.map((a) => a.name).join(", ")}
            </p>
          </div>
        )}
        {data.abstract && (
          <div>
            <p className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1">
              Abstract
            </p>
            <p className="text-xs text-zinc-300 leading-relaxed">
              {data.abstract}
            </p>
          </div>
        )}
        {data.llm_explanation && (
          <div>
            <p className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1">
              Relevance explanation
            </p>
            <p className="text-xs text-zinc-300 leading-relaxed">
              {data.llm_explanation}
            </p>
          </div>
        )}
        <div className="flex gap-2 mt-auto pt-2">
          {data.pdf_url && (
            <a
              href={data.pdf_url}
              target="_blank"
              rel="noreferrer"
              className="flex-1 text-center text-xs py-2 rounded border border-zinc-600 text-zinc-300 hover:bg-zinc-800 transition-colors"
            >
              PDF
            </a>
          )}
          {data.url && (
            <a
              href={data.url}
              target="_blank"
              rel="noreferrer"
              className="flex-1 text-center text-xs py-2 rounded border border-zinc-600 text-zinc-300 hover:bg-zinc-800 transition-colors"
            >
              Semantic Scholar
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

const LEGEND = [
  { label: "≥ 80%", color: "#10b981" },
  { label: "≥ 70%", color: "#84cc16" },
  { label: "≥ 60%", color: "#eab308" },
  { label: "< 60%", color: "#ef4444" },
];

function Legend() {
  return (
    <Panel position="top-right">
      <div className="bg-[var(--color-panel-bg)] border border-zinc-700 rounded-lg px-3 py-2 flex flex-col gap-1.5">
        <p className="text-[10px] text-zinc-500 uppercase tracking-wider">
          Relevance
        </p>
        {LEGEND.map(({ label, color }) => (
          <div key={label} className="flex items-center gap-2">
            <div
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ background: color }}
            />
            <span className="text-[11px] text-zinc-300">{label}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function FlowControls() {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const btnClass =
    "w-8 h-8 flex items-center justify-center bg-[var(--color-panel-bg)] border border-zinc-700 text-white hover:bg-zinc-800 cursor-pointer transition-colors text-sm";
  return (
    <Panel position="bottom-left">
      <div className="flex flex-col rounded-lg overflow-hidden border border-zinc-700">
        <button className={btnClass} onClick={() => zoomIn()}>
          +
        </button>
        <button className={btnClass} onClick={() => zoomOut()}>
          −
        </button>
        <button className={btnClass} onClick={() => fitView()}>
          ⊡
        </button>
      </div>
    </Panel>
  );
}

function FlowHeader({ onBack }: { onBack: () => void }) {
  return (
    <div className="p-6 pb-0">
      <header className="flex items-center justify-between px-6 py-4 bg-[var(--color-panel-bg)] rounded-lg">
        <div className="flex items-center gap-1 text-2xl font-semibold">
          RabbitHole
          <img src={rabbitLogo} alt="Logo" className="h-6 w-auto" />
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onBack}
            className="px-4 py-2 text-sm border border-zinc-600 rounded-lg bg-transparent text-white cursor-pointer hover:bg-zinc-800 transition-colors"
          >
            ← Back
          </button>
          <button
            type="button"
            className="px-4 py-2 text-sm border border-zinc-600 rounded-lg bg-transparent text-white cursor-pointer hover:bg-zinc-800 transition-colors"
          >
            Settings
          </button>
        </div>
      </header>
    </div>
  );
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

export function FlowPage({ onBack }: FlowPageProps) {
  const { nodes: initialNodes, edges } = toFlowGraph(MOCK_GRAPH.data);
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [selectedPaper, setSelectedPaper] = useState<PaperNodeData | null>(
    null,
  );

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  );

  const onNodeClick: NodeMouseHandler = useCallback((_e, node) => {
    setSelectedPaper(node.data as unknown as PaperNodeData);
  }, []);

  return (
    <>
      <style>{floatStyle}</style>
      <div className="h-screen flex flex-col bg-[var(--color-page-bg)] text-white">
        <FlowHeader onBack={onBack} />

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
                const d = node.data as unknown as PaperNodeData;
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
