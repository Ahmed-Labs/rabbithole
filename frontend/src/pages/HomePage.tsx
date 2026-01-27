import { useState } from "react";
import rabbitLogo from "../assets/rabbit-logo.png";

interface HomePageProps {
  onSearch: (query: string) => void;
}

export function HomePage({ onSearch }: HomePageProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <div className="min-h-screen bg-[#090D14] text-white flex flex-col">
      {/* Header Container Box */}
      <div className="p-6 pb-0">
        <header className="flex items-center justify-between px-6 py-4 bg-[#141E2D] rounded-lg">
          <div className="flex items-center gap-1 text-2xl font-semibold">
            RabbitHole
            <img
              src={rabbitLogo}
              alt="Logo"
              className="h-6 w-auto align-middle"
            />
          </div>
          <button className="px-4 py-2 border border-zinc-600 rounded-lg text-sm hover:bg-zinc-800 transition-colors">
            Settings
          </button>
        </header>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex items-start justify-center px-6 pt-12">
        <div className="w-full max-w-4xl bg-[#1b2838] rounded-2xl p-8">
          <p className="text-zinc-300 mb-6">
            Search papers and explore a knowledge graph of citations and
            relevance.
          </p>

          {/* Search Form */}
          <form onSubmit={handleSubmit}>
            {/* Search Input */}
            <input
              type="text"
              placeholder="Search by title, keywords,..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-4 py-3 bg-[#0d1b2a] border border-zinc-700 rounded-xl text-white placeholder-zinc-500 mb-4"
            />

            {/* Example and Button Row */}
            <div className="flex items-center justify-between mb-8">
              <span className="text-zinc-400 text-sm">E.g: "phasor"</span>
              <button
                type="submit"
                className="px-8 py-3 bg-orange-500 hover:bg-orange-400 text-white font-medium rounded-full transition-colors"
              >
                Search
              </button>
            </div>
          </form>

          {/* Graph Placeholder */}
          <div className="h-80 rounded-xl border border-zinc-700/50"></div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 text-zinc-500 text-sm">RabbitHole</footer>
    </div>
  );
}
