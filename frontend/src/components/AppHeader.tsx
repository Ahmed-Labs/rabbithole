import { useNavigate } from "react-router-dom";
import rabbitLogo from "../assets/rabbit-logo.png";

interface AppHeaderProps {
  showBack?: boolean;
  onBack?: () => void;
  showSearch?: boolean;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  onSearchSubmit?: () => void;
  searchPlaceholder?: string;
}

export function AppHeader({
  showBack = false,
  onBack,
  showSearch = false,
  searchValue = "",
  onSearchChange,
  onSearchSubmit,
  searchPlaceholder,
}: AppHeaderProps) {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 shrink-0 border-b border-border-default bg-page-bg/85 backdrop-blur">
      <div className="flex items-center gap-4 px-6 py-4">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="shrink-0 cursor-pointer"
          aria-label="Home"
          title="Home"
        >
          <img src={rabbitLogo} alt="Home" className="h-8 w-auto" />
        </button>

        {showSearch ? (
          <form
            className="flex-1"
            onSubmit={(e) => {
              e.preventDefault();
              onSearchSubmit?.();
            }}
          >
            <div
              className="
                flex items-center gap-3
                rounded-2xl
                border border-border-default
                bg-panel-bg
                px-4 py-3
                transition
                hover:border-border-default/80
                focus-within:ring-1 focus-within:ring-focus/30
              "
            >
              <svg
                viewBox="0 0 24 24"
                className="h-5 w-5 text-text-muted"
                aria-hidden="true"
              >
                <path
                  fill="currentColor"
                  d="M10 2a8 8 0 105.293 14.293l3.707 3.707a1 1 0 001.414-1.414l-3.707-3.707A8 8 0 0010 2zm-6 8a6 6 0 1110.39 3.39A6 6 0 014 10z"
                />
              </svg>

              <input
                value={searchValue}
                onChange={(e) => onSearchChange?.(e.target.value)}
                placeholder={searchPlaceholder ?? "Search papers…"}
                className="
                  w-full bg-transparent outline-none placeholder:text-placeholder
                  focus:outline-none focus:ring-0
                  focus-visible:outline-none focus-visible:ring-0
                "
              />
            </div>
          </form>
        ) : (
          <div className="flex-1" />
        )}

        {showBack && onBack ? (
          <button
            type="button"
            onClick={onBack}
            className={secondaryButtonClass}
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
        ) : null}
      </div>
    </header>
  );
}

const secondaryButtonClass = `
  inline-flex items-center gap-2
  rounded-xl border border-border-default
  bg-card-bg px-3 py-2
  text-sm font-medium text-text-secondary
  cursor-pointer transition
  hover:bg-content-bg/30 hover:text-text hover:border-border-default/80
  active:translate-y-[0.5px]
  focus-visible:ring-2 focus-visible:ring-focus/35
`;
