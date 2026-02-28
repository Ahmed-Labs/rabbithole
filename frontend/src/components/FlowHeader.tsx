import rabbitLogo from "../assets/rabbit-logo.png";

interface FlowHeaderProps {
  onBack: () => void;
}

export function FlowHeader({ onBack }: FlowHeaderProps) {
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
