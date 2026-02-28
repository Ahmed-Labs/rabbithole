import { Panel, useReactFlow } from "@xyflow/react";

export function FlowControls() {
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
