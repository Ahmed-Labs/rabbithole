import type { Node } from "@xyflow/react";

export interface PaperData {
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

export interface SchemaNode {
  id: string;
  type: "paperNode";
  position: { x: number; y: number };
  data: PaperData;
}

export interface SchemaEdge {
  id: string;
  source: string;
  target: string;
  type: "citationEdge";
  data: object;
}

export interface GraphData {
  nodes: SchemaNode[];
  edges: SchemaEdge[];
  root_id: string;
}

export interface GraphSchema {
  data: GraphData;
}

export type PaperNodeData = Record<string, unknown> & {
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
};

export type PaperFlowNode = Node<PaperNodeData, "paperNode">;
