import { useState } from "react";
import { useNavigate } from "react-router-dom";
import rabbitLogo from "../assets/rabbit-logo.png";

export function HomePage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const submit = (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    navigate(`/results?q=${encodeURIComponent(trimmed)}`);
  };

  return (
    <div className="min-h-screen bg-page-bg text-text">
      <main className="min-h-screen flex items-center justify-center px-6">
        <div className="w-full max-w-2xl -mt-10">
          <div className="flex flex-col items-center text-center mb-10">
            <img
              src={rabbitLogo}
              alt="RabbitHole"
              className="h-16 sm:h-20 w-auto"
            />
            <div className="mt-5 text-3xl sm:text-4xl font-semibold tracking-tight">
              RabbitHole
            </div>
            <p className="mt-3 text-sm sm:text-base text-text-secondary max-w-md">
              A research tool for finding relevant papers.
            </p>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(query);
            }}
          >
            <div
              className="
                w-full
                rounded-2xl
                border border-border-default
                bg-input-bg
                shadow-sm
                transition
                hover:shadow
                hover:-translate-y-px
                hover:border-border-default/80
                focus-within:shadow
                focus-within:translate-y-0
                focus-within:border-focus
                focus-within:ring-2 focus-within:ring-focus
              "
            >
              <div className="flex items-center gap-4 px-5 py-4">
                <svg
                  viewBox="0 0 24 24"
                  className="h-5 w-5 text-text-muted shrink-0"
                  aria-hidden="true"
                >
                  <path
                    fill="currentColor"
                    d="M10 2a8 8 0 105.293 14.293l3.707 3.707a1 1 0 001.414-1.414l-3.707-3.707A8 8 0 0010 2zm-6 8a6 6 0 1110.39 3.39A6 6 0 014 10z"
                  />
                </svg>

                <input
                  autoFocus
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by title, author, or keywords…"
                  className="
                    w-full bg-transparent outline-none
                    text-base sm:text-lg
                    placeholder:text-placeholder
                  "
                />
              </div>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
