import { useState } from "react";
import { ReactFlow, Background, Controls, MiniMap } from "@xyflow/react";
import type { Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { AnalysisOptions } from "../components/PaperPreview";
import rabbitLogo from "../assets/rabbit-logo.png";
import "./FlowPage.css";
import "../pages/ResultsPage.css";

interface FlowPageProps {
  analysisOptions: AnalysisOptions;
  onBack: () => void;
}

function buildInitialGraph(options: AnalysisOptions): {
  nodes: Node[];
  edges: Edge[];
} {
  const { paper, referenceDepth, includeCitations } = options;

  const nodes: Node[] = [
    {
      id: "root",
      type: "input",
      position: { x: 400, y: 0 },
      data: {
        label:
          paper.title.length > 40
            ? paper.title.slice(0, 40) + "…"
            : paper.title,
      },
      style: {
        background: "var(--color-border-accent)",
        color: "var(--color-text)",
        border: "none",
        borderRadius: 8,
        maxWidth: 220,
        whiteSpace: "normal" as const,
        textAlign: "center" as const,
      },
    },
  ];
  const edges: Edge[] = [];

  for (let depth = 1; depth <= referenceDepth; depth++) {
    const count = Math.max(1, 4 - depth);
    const xSpacing = 800 / (count + 1);

    for (let i = 0; i < count; i++) {
      const nodeId = `ref-d${depth}-${i}`;
      const parentId =
        depth === 1 ? "root" : `ref-d${depth - 1}-${Math.floor(i / 2)}`;

      nodes.push({
        id: nodeId,
        position: { x: xSpacing * (i + 1) - 40, y: depth * 160 },
        data: { label: `Reference (depth ${depth}, ${i + 1})` },
        style: {
          background: "var(--color-card-bg)",
          color: "var(--color-text)",
          border: `2px solid ${depth === 1 ? "var(--color-border-accent)" : "var(--color-focus)"}`,
          borderRadius: 8,
          maxWidth: 180,
          whiteSpace: "normal" as const,
          textAlign: "center" as const,
          fontSize: 12,
        },
      });

      edges.push({
        id: `e-${parentId}-${nodeId}`,
        source: parentId,
        target: nodeId,
        animated: depth === 1,
      });
    }
  }

  if (includeCitations) {
    nodes.push({
      id: "citations",
      type: "output",
      position: { x: 400, y: -160 },
      data: { label: `Papers citing "${paper.title.slice(0, 30)}…"` },
      style: {
        background: "var(--color-focus)",
        color: "var(--color-text)",
        border: "none",
        borderRadius: 8,
        maxWidth: 200,
        whiteSpace: "normal" as const,
        textAlign: "center" as const,
      },
    });
    edges.push({
      id: "e-citations-root",
      source: "citations",
      target: "root",
      animated: true,
    });
  }

  return { nodes, edges };
}

export function FlowPage({ analysisOptions, onBack }: FlowPageProps) {
  const { nodes, edges } = buildInitialGraph(analysisOptions);

  return (
    <div className="flow">
      <div className="results__header-wrap">
        <header className="results__header">
          <div className="results__brand">
            RabbitHole
            <img src={rabbitLogo} alt="Logo" className="results__logo" />
          </div>
          <div className="results__header-actions">
            <button
              type="button"
              onClick={onBack}
              className="results__header-btn"
            >
              ← Back
            </button>
            <button type="button" className="results__header-btn">
              Settings
            </button>
          </div>
        </header>
      </div>

      <div className="flow__canvas-wrap">
        <div className="flow__react-flow">
          <ReactFlow nodes={nodes} edges={edges} fitView>
            {/* <Background color="var(--color-border-default)" gap={20} /> */}
            <Controls />
            <MiniMap
              nodeColor={(node) =>
                node.id === "root" || node.id === "citations"
                  ? "#3621f6"
                  : "#6366f1"
              }
              nodeStrokeWidth={0}
              maskColor="rgba(9,13,20,0.6)"
            />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
