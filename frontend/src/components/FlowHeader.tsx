import { useNavigate } from "react-router-dom";
import rabbitLogo from "../assets/rabbit-logo.png";

interface FlowHeaderProps {
  onBack: () => void;
}

export function FlowHeader({ onBack }: FlowHeaderProps) {
  const navigate = useNavigate();

  return (
    <header className="shrink-0 sticky top-0 z-50 bg-page-bg/85 backdrop-blur border-b border-border-default">
      <div className="px-6 py-4 flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="shrink-0 cursor-pointer"
          aria-label="Home"
          title="Home"
        >
          <img src={rabbitLogo} alt="Home" className="h-8 w-auto" />
        </button>

        <button
          type="button"
          onClick={onBack}
          className="
            inline-flex items-center gap-2
            px-3 py-2 rounded-xl
            bg-card-bg border border-border-default
            text-text-secondary text-sm font-medium
            cursor-pointer transition
            hover:bg-content-bg/30 hover:text-text hover:border-border-default/80
            active:translate-y-[0.5px]
            focus-visible:ring-2 focus-visible:ring-focus/35
          "
          aria-label="Go back"
        >
          <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
            <path
              d="M12.5 15.5L7 10l5.5-5.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Back
        </button>
      </div>
    </header>
  );
}
