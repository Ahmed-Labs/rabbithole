import { memo } from "react";
import {
  ReactFlow,
  Background,
  MiniMap,
  Panel,
  useReactFlow,
  Handle,
  Position,
} from "@xyflow/react";
import type { Node, Edge, NodeTypes } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { AnalysisOptions } from "../components/PaperPreview";
import rabbitLogo from "../assets/rabbit-logo.png";

interface FlowPageProps {
  analysisOptions: AnalysisOptions;
  onBack: () => void;
}

const PaperNode = memo(({ data }: { data: { label: string } }) => (
  <div className="px-3 py-2 rounded border border-zinc-600 bg-[var(--color-card-bg)] text-white text-xs w-40">
    <Handle type="target" position={Position.Top} />
    {data.label}
    <Handle type="source" position={Position.Bottom} />
  </div>
));

const nodeTypes: NodeTypes = { paper: PaperNode };

function buildInitialGraph(options: AnalysisOptions): {
  nodes: Node[];
  edges: Edge[];
} {
  const { paper, referenceDepth } = options;

  const nodes: Node[] = [
    {
      id: "root",
      type: "paper",
      position: { x: 400, y: 0 },
      data: {
        label:
          paper.title.length > 40
            ? paper.title.slice(0, 40) + "…"
            : paper.title,
      },
    },
  ];
  const edges: Edge[] = [];

  for (let depth = 1; depth <= referenceDepth; depth++) {
    const count = Math.max(1, 4 - depth);
    const xSpacing = 800 / (count + 1);

    for (let i = 0; i < count; i++) {
      const nodeId = `node-d${depth}-${i}`;
      const parentId =
        depth === 1 ? "root" : `node-d${depth - 1}-${Math.floor(i / 2)}`;

      nodes.push({
        id: nodeId,
        type: "paper",
        position: { x: xSpacing * (i + 1) - 40, y: depth * 160 },
        data: { label: `Paper ${depth}-${i + 1}` },
      });

      edges.push({
        id: `e-${parentId}-${nodeId}`,
        source: parentId,
        target: nodeId,
      });
    }
  }

  return { nodes, edges };
}

function FlowControls() {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const btnClass =
    "w-8 h-8 flex items-center justify-center bg-[var(--color-panel-bg)] border border-zinc-700 text-white hover:bg-[var(--color-card-bg)] cursor-pointer transition-colors text-sm";
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

export function FlowPage({ analysisOptions, onBack }: FlowPageProps) {
  const { nodes, edges } = buildInitialGraph(analysisOptions);

  return (
    <div className="h-screen flex flex-col bg-[var(--color-page-bg)] text-white">
      <FlowHeader onBack={onBack} />

      <div className="flex-1 min-h-0 m-6 rounded-lg overflow-hidden bg-[var(--color-input-bg-dark)] flex flex-col">
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
          <Background color="var(--color-border-default)" gap={20} />
          <FlowControls />
          <MiniMap
            className="!bg-[var(--color-panel-bg)] !border !border-zinc-700 rounded-lg"
            nodeColor="#3621f6"
            nodeStrokeWidth={0}
            maskColor="rgba(9,13,20,0.6)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}
