import { PaperNode } from "../components/PaperNode";
import type { Edge, NodeTypes } from "@xyflow/react";
import type { GraphData, PaperFlowNode } from "../types/graph";
import dagre from "dagre";

export const nodeTypes: NodeTypes = { paperNode: PaperNode };

const NODE_W = 210;
const NODE_H = 100;

export function toFlowGraph(schema: GraphData): {
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

export function toCompactFlowGraph(schema: GraphData): {
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

  // Horizontal ordering by relevance scores
  const relevance = new Map<string, number>();
  schema.nodes.forEach((n) => relevance.set(n.id, n.data.relevance_score ?? 0));

  // Bucket nodes by depth using their y position from dagre
  const layerBuckets = new Map<number, string[]>();
  for (const n of schema.nodes) {
    const pos = g.node(n.id) as { x: number; y: number };
    const layerKey = Math.round(pos.y);
    const arr = layerBuckets.get(layerKey) ?? [];
    arr.push(n.id);
    layerBuckets.set(layerKey, arr);
  }

  // Arrange IDs so highest relevance ends up near the center
  function centerOut(ids: string[]) {
    if (ids.length <= 1) return ids;
    const res = new Array(ids.length);
    const mid = Math.floor(ids.length / 2);
    let left = mid - 1;
    let right = mid + 1;

    res[mid] = ids[0];
    for (let i = 1; i < ids.length; i++) {
      if (i % 2 === 1) res[right++] = ids[i];
      else res[left--] = ids[i];
    }
    return res.filter(Boolean) as string[];
  }

  // New x positions for nodes (relative to root)
  const forcedX = new Map<string, number>();

  // Root stays at x=0
  forcedX.set(schema.root_id, 0);

  // spacing between siblings in same layer
  const SPACING_X = NODE_W + 60;

  // For each layer sort by relevance desc
  for (const [, ids] of layerBuckets.entries()) {
    const filtered = ids.filter((id) => id !== schema.root_id);

    filtered.sort((a, b) => (relevance.get(b) ?? 0) - (relevance.get(a) ?? 0));
    const ordered = centerOut(filtered);

    // Assign x positions so the *middle index* is closest to x=0
    const n = ordered.length;
    for (let i = 0; i < n; i++) {
      const x = (i - (n - 1) / 2) * SPACING_X; // symmetric around 0
      forcedX.set(ordered[i], x);
    }
  }

  const rootNode = g.node(schema.root_id) as
    | { x: number; y: number }
    | undefined;
  const offsetY = rootNode ? rootNode.y : 0;

  const nodes: PaperFlowNode[] = schema.nodes.map((n) => {
    const { y } = g.node(n.id) as { x: number; y: number };

    const xForced = forcedX.get(n.id);
    const x =
      xForced !== undefined
        ? xForced
        : (g.node(n.id) as { x: number; y: number }).x -
          (rootNode ? rootNode.x : 0);

    return {
      id: n.id,
      type: "paperNode",
      position: { x, y: y - offsetY },
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
