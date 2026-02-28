import { useState } from "react";
import { useNavigate } from "react-router-dom";
import rabbitLogo from "../assets/rabbit-logo.png";

export function HomePage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/results?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-page-bg text-text flex flex-col">
      <div className="px-6 pt-6">
        <header className="flex items-center justify-between px-6 py-4 bg-panel-bg rounded-lg">
          <div className="flex items-center gap-1 text-2xl font-semibold">
            RabbitHole
            <img src={rabbitLogo} alt="Logo" className="h-6 w-auto" />
          </div>
          <button
            type="button"
            className="px-4 py-2 text-sm border border-zinc-600 rounded-lg bg-transparent text-text cursor-pointer hover:bg-zinc-800 transition-colors"
          >
            Settings
          </button>
        </header>
      </div>

      <main className="flex-1 flex items-start justify-center p-6 pb-12">
        <div className="w-full max-w-4xl bg-content-bg rounded-2xl p-8">
          <p className="text-text-secondary mb-6">
            Search papers and explore a knowledge graph of citations and
            relevance.
          </p>

          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Search by title, keywords,..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-4 py-3 bg-input-bg border border-border-default rounded-xl text-text placeholder:text-placeholder mb-4 focus:outline-none focus:ring-2 focus:ring-focus"
            />
            <div className="flex items-center justify-between mb-8">
              <span className="text-text-muted text-sm">E.g: "phasor"</span>
              <button
                type="submit"
                className="px-8 py-3 bg-primary text-text font-medium rounded-full cursor-pointer hover:bg-primary-hover transition-colors"
              >
                Search
              </button>
            </div>
          </form>

          <div className="h-80 rounded-xl border border-zinc-700/50" />
        </div>
      </main>

      <footer className="px-6 py-4 text-placeholder text-sm">RabbitHole</footer>
    </div>
  );
}
