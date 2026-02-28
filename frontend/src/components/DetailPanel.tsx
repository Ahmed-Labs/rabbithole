import type { PaperNodeData } from "../types/graph";
import { relevanceColor } from "../utils/relevanceColor";

interface DetailPanelProps {
  data: PaperNodeData;
  onClose: () => void;
}

export function DetailPanel({ data, onClose }: DetailPanelProps) {
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
