import { memo, useState, useCallback } from "react";
import { ReactFlow, Background, MiniMap, Panel, useReactFlow, Handle, Position } from "@xyflow/react";
import type { Node, Edge, NodeTypes, NodeMouseHandler } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import rabbitLogo from "../assets/rabbit-logo.png";

interface FlowPageProps {
  onBack: () => void;
}

// ── Schema types ──────────────────────────────────────────────────────────────

interface PaperData {
  id: string;
  title: string;
  abstract: string;
  authors: string[];
  year: number;
  citation_count: number;
  relevance_score: number;
  is_root: boolean;
  pdf_url: string;
  url: string;
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

interface GraphSchema {
  nodes: SchemaNode[];
  edges: SchemaEdge[];
  root_id: string;
}

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_GRAPH: GraphSchema = {"edges":[{"data":{},"id":"cite-23c12c4e47dff279db5a632f4830adc02eddecff-90f50c33f687622b00b260fd178c83ecf084291b","source":"23c12c4e47dff279db5a632f4830adc02eddecff","target":"90f50c33f687622b00b260fd178c83ecf084291b","type":"citationEdge"},{"data":{},"id":"cite-c08bb5d4aa8b8b4a429f571cb9bd524fdc5f8f29-90f50c33f687622b00b260fd178c83ecf084291b","source":"c08bb5d4aa8b8b4a429f571cb9bd524fdc5f8f29","target":"90f50c33f687622b00b260fd178c83ecf084291b","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-1994f886b74aff3ef31802769f2c502dbe0b25aa","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"1994f886b74aff3ef31802769f2c502dbe0b25aa","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-f9d727d2cd57bd7e96007368ff2fb3c49fa2ed1d","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"f9d727d2cd57bd7e96007368ff2fb3c49fa2ed1d","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-e7cd36d4c8366d9bb0cdbfa5af81fa5e0d9dba2f","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"e7cd36d4c8366d9bb0cdbfa5af81fa5e0d9dba2f","type":"citationEdge"},{"data":{},"id":"cite-638d8d1f3865ebf065605535a7aa50727d5ffabe-90f50c33f687622b00b260fd178c83ecf084291b","source":"638d8d1f3865ebf065605535a7aa50727d5ffabe","target":"90f50c33f687622b00b260fd178c83ecf084291b","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-4be040c953d8580f0127105924a8bbf139c4804d","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"4be040c953d8580f0127105924a8bbf139c4804d","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-4eec2589ee1eeb8e08c16334b8fd2fad5b32446e","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"4eec2589ee1eeb8e08c16334b8fd2fad5b32446e","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-5ad057577eac072aa70776c8faf83ef9787ab60c","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"5ad057577eac072aa70776c8faf83ef9787ab60c","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-75d7591078a74aa6bfcdaf5bde7dbe5146a45ecd","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"75d7591078a74aa6bfcdaf5bde7dbe5146a45ecd","type":"citationEdge"},{"data":{},"id":"cite-b7c6c57f9c8668b224e5fefc2ca93345392a62b6-90f50c33f687622b00b260fd178c83ecf084291b","source":"b7c6c57f9c8668b224e5fefc2ca93345392a62b6","target":"90f50c33f687622b00b260fd178c83ecf084291b","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-7b248d78573ccf0dca6aa2cec2743d3eccaa9d1a","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"7b248d78573ccf0dca6aa2cec2743d3eccaa9d1a","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-c94b65f043c792e576f0be7cfa216dcfaf724337","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"c94b65f043c792e576f0be7cfa216dcfaf724337","type":"citationEdge"},{"data":{},"id":"cite-90f50c33f687622b00b260fd178c83ecf084291b-fe1cdf9d438af4b31e7d7cb3f53d2d3684f4f704","source":"90f50c33f687622b00b260fd178c83ecf084291b","target":"fe1cdf9d438af4b31e7d7cb3f53d2d3684f4f704","type":"citationEdge"},{"data":{},"id":"cite-6ec20a6b21de7f86464a025bee67cc882080fd1e-90f50c33f687622b00b260fd178c83ecf084291b","source":"6ec20a6b21de7f86464a025bee67cc882080fd1e","target":"90f50c33f687622b00b260fd178c83ecf084291b","type":"citationEdge"}],"nodes":[{"data":{"abstract":"While language models have become impactful, video generation remains largely confined to entertainment.","authors":["Junhao Cheng","Liang Hou"],"citation_count":1,"id":"23c12c4e47dff279db5a632f4830adc02eddecff","is_root":false,"pdf_url":"https://arxiv.org/pdf/2511.16669.pdf","relevance_score":0.82,"title":"Video-as-Answer: Predict and Generate Next Video Event with Joint-GRPO","url":"https://www.semanticscholar.org/paper/23c12c4e47dff279db5a632f4830adc02eddecff","year":2025},"id":"23c12c4e47dff279db5a632f4830adc02eddecff","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"We introduce PlayerOne, the first egocentric realistic world simulator.","authors":["Yuanpeng Tu","Hao Luo"],"citation_count":3,"id":"c08bb5d4aa8b8b4a429f571cb9bd524fdc5f8f29","is_root":false,"pdf_url":"https://arxiv.org/pdf/2506.09995.pdf","relevance_score":0.78,"title":"PlayerOne: Egocentric World Simulator","url":"https://www.semanticscholar.org/paper/c08bb5d4aa8b8b4a429f571cb9bd524fdc5f8f29","year":2025},"id":"c08bb5d4aa8b8b4a429f571cb9bd524fdc5f8f29","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"GameFactory is a framework for action-controlled scene-generalizable game video generation.","authors":["Jiwen Yu","Yiran Qin"],"citation_count":60,"id":"1994f886b74aff3ef31802769f2c502dbe0b25aa","is_root":false,"pdf_url":"https://arxiv.org/pdf/2501.08325.pdf","relevance_score":0.84,"title":"GameFactory: Creating New Games with Generative Interactive Videos","url":"https://www.semanticscholar.org/paper/1994f886b74aff3ef31802769f2c502dbe0b25aa","year":2025},"id":"1994f886b74aff3ef31802769f2c502dbe0b25aa","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"Divot leverages the diffusion process for self-supervised video representation learning.","authors":["Yuying Ge","Yizhuo Li"],"citation_count":7,"id":"f9d727d2cd57bd7e96007368ff2fb3c49fa2ed1d","is_root":false,"pdf_url":"https://arxiv.org/pdf/2412.04432.pdf","relevance_score":0.76,"title":"Divot: Diffusion Powers Video Tokenizer for Comprehension and Generation","url":"https://www.semanticscholar.org/paper/f9d727d2cd57bd7e96007368ff2fb3c49fa2ed1d","year":2024},"id":"f9d727d2cd57bd7e96007368ff2fb3c49fa2ed1d","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"Patchview is a customizable LLM-powered system that visually aids worldbuilding.","authors":["John Joon Young Chung","Max Kreminski"],"citation_count":30,"id":"e7cd36d4c8366d9bb0cdbfa5af81fa5e0d9dba2f","is_root":false,"pdf_url":"https://arxiv.org/pdf/2408.04112.pdf","relevance_score":0.78,"title":"Patchview: LLM-powered Worldbuilding with Generative Dust and Magnet Visualization","url":"https://www.semanticscholar.org/paper/e7cd36d4c8366d9bb0cdbfa5af81fa5e0d9dba2f","year":2024},"id":"e7cd36d4c8366d9bb0cdbfa5af81fa5e0d9dba2f","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"TheaterGen integrates LLMs and text-to-image models for multi-turn image generation.","authors":["Junhao Cheng","Baiqiao Yin"],"citation_count":19,"id":"638d8d1f3865ebf065605535a7aa50727d5ffabe","is_root":false,"pdf_url":"https://arxiv.org/pdf/2404.18919.pdf","relevance_score":0.82,"title":"TheaterGen: Character Management with LLM for Consistent Multi-turn Image Generation","url":"https://www.semanticscholar.org/paper/638d8d1f3865ebf065605535a7aa50727d5ffabe","year":2024},"id":"638d8d1f3865ebf065605535a7aa50727d5ffabe","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"Unbounded uses generative models to create a game of character life simulation.","authors":["Jialu Li","Yuanzhen Li"],"citation_count":12,"id":"4be040c953d8580f0127105924a8bbf139c4804d","is_root":false,"pdf_url":"https://arxiv.org/pdf/2410.18975.pdf","relevance_score":0.85,"title":"Unbounded: A Generative Infinite Game of Character Life Simulation","url":"https://www.semanticscholar.org/paper/4be040c953d8580f0127105924a8bbf139c4804d","year":2024},"id":"4be040c953d8580f0127105924a8bbf139c4804d","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"An enhanced Transformer module for open-ended story visualization using separate attention mechanisms.","authors":["Xiangyang Luo","Junhao Cheng"],"citation_count":8,"id":"4eec2589ee1eeb8e08c16334b8fd2fad5b32446e","is_root":false,"pdf_url":"https://arxiv.org/pdf/2503.23353.pdf","relevance_score":0.82,"title":"Object Isolated Attention for Consistent Story Visualization","url":"https://www.semanticscholar.org/paper/4eec2589ee1eeb8e08c16334b8fd2fad5b32446e","year":2025},"id":"4eec2589ee1eeb8e08c16334b8fd2fad5b32446e","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"PlayGen proposes a novel method for generating playable games using an autoregressive DiT-based diffusion model.","authors":["Mingyu Yang","Junyou Li"],"citation_count":19,"id":"5ad057577eac072aa70776c8faf83ef9787ab60c","is_root":false,"pdf_url":"https://arxiv.org/pdf/2412.00887.pdf","relevance_score":0.84,"title":"Playable Game Generation","url":"https://www.semanticscholar.org/paper/5ad057577eac072aa70776c8faf83ef9787ab60c","year":2024},"id":"5ad057577eac072aa70776c8faf83ef9787ab60c","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"GameNGen is the first game engine powered entirely by a neural model enabling real-time interaction.","authors":["Dani Valevski","Yaniv Leviathan"],"citation_count":156,"id":"75d7591078a74aa6bfcdaf5bde7dbe5146a45ecd","is_root":false,"pdf_url":"https://arxiv.org/pdf/2408.14837.pdf","relevance_score":0.78,"title":"Diffusion Models Are Real-Time Game Engines","url":"https://www.semanticscholar.org/paper/75d7591078a74aa6bfcdaf5bde7dbe5146a45ecd","year":2024},"id":"75d7591078a74aa6bfcdaf5bde7dbe5146a45ecd","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"AnimeShooter is a reference-guided multi-shot animation dataset with comprehensive hierarchical annotations.","authors":["Lu Qiu","Yizhuo Li"],"citation_count":1,"id":"b7c6c57f9c8668b224e5fefc2ca93345392a62b6","is_root":false,"pdf_url":"https://arxiv.org/pdf/2506.03126.pdf","relevance_score":0.86,"title":"AnimeShooter: A Multi-Shot Animation Dataset for Reference-Guided Video Generation","url":"https://www.semanticscholar.org/paper/b7c6c57f9c8668b224e5fefc2ca93345392a62b6","year":2025},"id":"b7c6c57f9c8668b224e5fefc2ca93345392a62b6","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"CogVideoX is a large-scale text-to-video generation model based on diffusion transformer.","authors":["Zhuoyi Yang","Jiayan Teng"],"citation_count":1297,"id":"7b248d78573ccf0dca6aa2cec2743d3eccaa9d1a","is_root":false,"pdf_url":"https://arxiv.org/pdf/2408.06072.pdf","relevance_score":0.83,"title":"CogVideoX: Text-to-Video Diffusion Models with An Expert Transformer","url":"https://www.semanticscholar.org/paper/7b248d78573ccf0dca6aa2cec2743d3eccaa9d1a","year":2024},"id":"7b248d78573ccf0dca6aa2cec2743d3eccaa9d1a","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"A large-scale cooking video dataset designed to advance long-form narrative generation.","authors":["Junfei Xiao","Feng Cheng"],"citation_count":7,"id":"c94b65f043c792e576f0be7cfa216dcfaf724337","is_root":false,"pdf_url":"https://arxiv.org/pdf/2501.06173.pdf","relevance_score":0.77,"title":"VideoAuteur: Towards Long Narrative Video Generation","url":"https://www.semanticscholar.org/paper/c94b65f043c792e576f0be7cfa216dcfaf724337","year":2025},"id":"c94b65f043c792e576f0be7cfa216dcfaf724337","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"GameGen-X is the first diffusion transformer model for generating and interactively controlling open-world game videos.","authors":["Haoxuan Che","Xuanhua He"],"citation_count":66,"id":"fe1cdf9d438af4b31e7d7cb3f53d2d3684f4f704","is_root":false,"pdf_url":"https://arxiv.org/pdf/2411.00769.pdf","relevance_score":0.85,"title":"GameGen-X: Interactive Open-world Game Video Generation","url":"https://www.semanticscholar.org/paper/fe1cdf9d438af4b31e7d7cb3f53d2d3684f4f704","year":2024},"id":"fe1cdf9d438af4b31e7d7cb3f53d2d3684f4f704","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"AutoStudio is a training-free multi-agent framework for multi-turn interactive image generation.","authors":["Junhao Cheng","Xi Lu"],"citation_count":16,"id":"6ec20a6b21de7f86464a025bee67cc882080fd1e","is_root":false,"pdf_url":"https://arxiv.org/pdf/2406.01388.pdf","relevance_score":0.85,"title":"AutoStudio: Crafting Consistent Subjects in Multi-turn Interactive Image Generation","url":"https://www.semanticscholar.org/paper/6ec20a6b21de7f86464a025bee67cc882080fd1e","year":2024},"id":"6ec20a6b21de7f86464a025bee67cc882080fd1e","position":{"x":0,"y":0},"type":"paperNode"},{"data":{"abstract":"AnimeGamer is built upon Multimodal Large Language Models to generate each game state as dynamic animation shots.","authors":["Junhao Cheng","Yuying Ge"],"citation_count":5,"id":"90f50c33f687622b00b260fd178c83ecf084291b","is_root":true,"pdf_url":"https://arxiv.org/pdf/2504.01014.pdf","relevance_score":0.0,"title":"AnimeGamer: Infinite Anime Life Simulation with Next Game State Prediction","url":"https://www.semanticscholar.org/paper/90f50c33f687622b00b260fd178c83ecf084291b","year":2025},"id":"90f50c33f687622b00b260fd178c83ecf084291b","position":{"x":0,"y":0},"type":"paperNode"}],"root_id":"90f50c33f687622b00b260fd178c83ecf084291b"};

// ── Relevance color ───────────────────────────────────────────────────────────

function relevanceColor(score: number): string {
  if (score >= 0.8) return "#10b981";  // emerald
  if (score >= 0.7) return "#84cc16";  // lime
  if (score >= 0.6) return "#eab308";  // yellow
  if (score >= 0.5) return "#f59e0b";  // amber
  if (score >= 0.4) return "#f97316";  // orange
  if (score >= 0.3) return "#ef4444";  // red-orange
  return "#dc2626";                    // red
}

// ── Layout ────────────────────────────────────────────────────────────────────

function computePositions(schema: GraphSchema): Record<string, { x: number; y: number }> {
  const NODE_W = 240;
  const NODE_H = 180;
  const { root_id, edges } = schema;

  const above = edges.filter((e) => e.target === root_id).map((e) => e.source);
  const below = edges.filter((e) => e.source === root_id).map((e) => e.target);

  const positions: Record<string, { x: number; y: number }> = {};
  const spreadX = (ids: string[], y: number) =>
    ids.forEach((id, i) => {
      positions[id] = { x: (i - (ids.length - 1) / 2) * NODE_W, y };
    });

  positions[root_id] = { x: 0, y: 0 };
  spreadX(above, -NODE_H);
  spreadX(below, NODE_H);

  return positions;
}

// ── Schema → ReactFlow ────────────────────────────────────────────────────────

function toFlowGraph(schema: GraphSchema): { nodes: Node[]; edges: Edge[] } {
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
    },
  }));

  const edges: Edge[] = schema.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    style: { stroke: "#3f3f46", strokeWidth: 1.5 },
  }));

  return { nodes, edges };
}

// ── PaperNode ─────────────────────────────────────────────────────────────────

interface PaperNodeData {
  title: string;
  year: number;
  citation_count: number;
  relevance_score: number;
  abstract: string;
  authors: string[];
  pdf_url: string;
  url: string;
  isRoot: boolean;
}

const PaperNode = memo(({ data }: { data: PaperNodeData }) => {
  const color = data.isRoot ? "#818cf8" : relevanceColor(data.relevance_score);
  return (
    <div
      className="rounded-lg bg-[var(--color-card-bg)] text-white text-xs w-52 cursor-pointer"
      style={{ border: `2px solid ${color}` }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color, border: "none" }} />

      {/* Colored top bar */}
      <div className="h-1 rounded-t-md" style={{ background: color }} />

      <div className="p-3 flex flex-col gap-1">
        <p className="font-semibold leading-snug line-clamp-3 text-[11px]">{data.title}</p>
        <div className="flex items-center justify-between mt-1">
          <span className="text-zinc-400 text-[10px]">{data.year}</span>
          {!data.isRoot && (
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded" style={{ background: color + "22", color }}>
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

      <Handle type="source" position={Position.Bottom} style={{ background: color, border: "none" }} />
    </div>
  );
});

const nodeTypes: NodeTypes = { paperNode: PaperNode };

// ── Detail panel shown on node click ─────────────────────────────────────────

function DetailPanel({ data, onClose }: { data: PaperNodeData; onClose: () => void }) {
  const color = data.isRoot ? "#818cf8" : relevanceColor(data.relevance_score);
  return (
    <div className="absolute top-0 right-0 h-full w-80 bg-[var(--color-panel-bg)] border-l border-zinc-700 flex flex-col z-10 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-700">
        <span className="text-sm font-semibold text-white">Paper details</span>
        <button onClick={onClose} className="text-zinc-400 hover:text-white transition-colors text-lg leading-none">×</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {/* Title + badges */}
        <div>
          <h3 className="text-sm font-semibold text-white leading-snug mb-2">{data.title}</h3>
          <div className="flex flex-wrap gap-2">
            <span className="text-[11px] text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">{data.year}</span>
            <span className="text-[11px] text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">{data.citation_count} citations</span>
            {!data.isRoot && (
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded" style={{ background: color + "22", color }}>
                {(data.relevance_score * 100).toFixed(0)}% relevant
              </span>
            )}
          </div>
        </div>

        {/* Authors */}
        {data.authors.length > 0 && (
          <div>
            <p className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1">Authors</p>
            <p className="text-xs text-zinc-300">{data.authors.join(", ")}</p>
          </div>
        )}

        {/* Abstract */}
        {data.abstract && (
          <div>
            <p className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1">Abstract</p>
            <p className="text-xs text-zinc-300 leading-relaxed">{data.abstract}</p>
          </div>
        )}

        {/* Links */}
        <div className="flex gap-2 mt-auto pt-2">
          {data.pdf_url && (
            <a href={data.pdf_url} target="_blank" rel="noreferrer"
              className="flex-1 text-center text-xs py-2 rounded border border-zinc-600 text-zinc-300 hover:bg-zinc-800 transition-colors">
              PDF
            </a>
          )}
          {data.url && (
            <a href={data.url} target="_blank" rel="noreferrer"
              className="flex-1 text-center text-xs py-2 rounded border border-zinc-600 text-zinc-300 hover:bg-zinc-800 transition-colors">
              Semantic Scholar
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Legend ────────────────────────────────────────────────────────────────────

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
        <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Relevance</p>
        {LEGEND.map(({ label, color }) => (
          <div key={label} className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: color }} />
            <span className="text-[11px] text-zinc-300">{label}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ── FlowControls ──────────────────────────────────────────────────────────────

function FlowControls() {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const btnClass =
    "w-8 h-8 flex items-center justify-center bg-[var(--color-panel-bg)] border border-zinc-700 text-white hover:bg-zinc-800 cursor-pointer transition-colors text-sm";
  return (
    <Panel position="bottom-left">
      <div className="flex flex-col rounded-lg overflow-hidden border border-zinc-700">
        <button className={btnClass} onClick={() => zoomIn()}>+</button>
        <button className={btnClass} onClick={() => zoomOut()}>−</button>
        <button className={btnClass} onClick={() => fitView()}>⊡</button>
      </div>
    </Panel>
  );
}

// ── FlowHeader ────────────────────────────────────────────────────────────────

function FlowHeader({ onBack }: { onBack: () => void }) {
  return (
    <div className="p-6 pb-0">
      <header className="flex items-center justify-between px-6 py-4 bg-[var(--color-panel-bg)] rounded-lg">
        <div className="flex items-center gap-1 text-2xl font-semibold">
          RabbitHole
          <img src={rabbitLogo} alt="Logo" className="h-6 w-auto" />
        </div>
        <div className="flex gap-3">
          <button type="button" onClick={onBack}
            className="px-4 py-2 text-sm border border-zinc-600 rounded-lg bg-transparent text-white cursor-pointer hover:bg-zinc-800 transition-colors">
            ← Back
          </button>
          <button type="button"
            className="px-4 py-2 text-sm border border-zinc-600 rounded-lg bg-transparent text-white cursor-pointer hover:bg-zinc-800 transition-colors">
            Settings
          </button>
        </div>
      </header>
    </div>
  );
}

// ── FlowPage ──────────────────────────────────────────────────────────────────

export function FlowPage({ onBack }: FlowPageProps) {
  const { nodes, edges } = toFlowGraph(MOCK_GRAPH);
  const [selectedPaper, setSelectedPaper] = useState<PaperNodeData | null>(null);

  const onNodeClick: NodeMouseHandler = useCallback((_e, node) => {
    setSelectedPaper(node.data as PaperNodeData);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-[var(--color-page-bg)] text-white">
      <FlowHeader onBack={onBack} />

      <div className="flex-1 min-h-0 m-6 rounded-lg overflow-hidden bg-[var(--color-input-bg-dark)] flex flex-col relative">
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodeClick={onNodeClick} fitView>
          <Background color="var(--color-border-default)" gap={20} />
          <FlowControls />
          <Legend />
          <MiniMap
            className="!bg-[var(--color-panel-bg)] !border !border-zinc-700 rounded-lg"
            nodeColor={(node) => {
              const d = node.data as PaperNodeData;
              return d.isRoot ? "#818cf8" : relevanceColor(d.relevance_score);
            }}
            nodeStrokeWidth={0}
            maskColor="rgba(9,13,20,0.6)"
          />
        </ReactFlow>

        {selectedPaper && (
          <DetailPanel data={selectedPaper} onClose={() => setSelectedPaper(null)} />
        )}
      </div>
    </div>
  );
}