import { Panel } from "@xyflow/react";

const LEGEND = [
  { label: "≥ 80%", color: "#10b981" },
  { label: "≥ 70%", color: "#84cc16" },
  { label: "≥ 60%", color: "#eab308" },
  { label: "< 60%", color: "#ef4444" },
];

export function Legend() {
  return (
    <Panel position="top-right">
      <div className="bg-panel-bg border border-zinc-700 rounded-lg px-3 py-2 flex flex-col gap-1.5">
        <p className="text-[10px] text-zinc-500 uppercase tracking-wider">
          Relevance
        </p>
        {LEGEND.map(({ label, color }) => (
          <div key={label} className="flex items-center gap-2">
            <div
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{ background: color }}
            />
            <span className="text-[11px] text-zinc-300">{label}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}
