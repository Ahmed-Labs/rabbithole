import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import type { PaperNodeData } from "../types/graph";
import { relevanceColor } from "../utils/relevanceColor";

export const PaperNode = memo(({ data }: { data: PaperNodeData }) => {
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
