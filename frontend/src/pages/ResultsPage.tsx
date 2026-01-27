import { useState, useEffect, useRef } from "react";
import rabbitLogo from "../assets/rabbit-logo.png";
import type { Paper } from "../types/Paper";
import { PaperCard } from "../components/PaperCard";
import { PaperPreview } from "../components/PaperPreview";

interface ResultsPageProps {
  searchQuery: string;
  onNewSearch: () => void;
}

export function ResultsPage({ searchQuery, onNewSearch }: ResultsPageProps) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [filterQuery, setFilterQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const previewScrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mapPaper = (p: {
      id: string;
      title: string;
      authors: { name: string; authorId?: string }[];
      abstract: string;
      year: number | null;
      citation_count?: number | null;
      pdf_url?: string | null;
      url: string;
    }): Paper => ({
      id: p.id,
      title: p.title,
      authors: p.authors ?? [],
      abstract: p.abstract ?? "",
      year: p.year ?? null,
      citationCount: p.citation_count ?? 0,
      pdfUrl: p.pdf_url ?? null,
      url: p.url,
    });

    const fetchPapers = async () => {
      setLoading(true);
      setError(null);
      try {
        const url = `/api/search?query=${encodeURIComponent(searchQuery)}`;
        const response = await fetch(url);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.error || `Failed to search papers (${response.status})`,
          );
        }

        const data = await response.json();
        const list = (data.papers ?? []).map(mapPaper);
        setPapers(list);
        if (list.length > 0) {
          setSelectedPaper(list[0]);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Unknown error occurred. Make sure the Flask backend is running on port 5000.";
        setError(errorMessage);
        console.error("Search error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchPapers();
  }, [searchQuery]);

  const filteredPapers = papers.filter((paper) =>
    paper.title.toLowerCase().includes(filterQuery.toLowerCase()),
  );

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
          <div className="flex gap-3">
            <button
              onClick={onNewSearch}
              className="px-4 py-2 border border-zinc-600 rounded-lg text-sm hover:bg-zinc-800 transition-colors"
            >
              New search
            </button>
            <button className="px-4 py-2 border border-zinc-600 rounded-lg text-sm hover:bg-zinc-800 transition-colors">
              Settings
            </button>
          </div>
        </header>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden p-6 gap-6 items-stretch">
        {/* Left Panel - Results */}
        <aside className="w-1/3 flex flex-col">
          {/* Results Container Box */}
          <div className="flex-1 min-h-0 flex flex-col bg-[#101723] rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-3 text-white">Results</h2>
            <input
              type="text"
              placeholder="Search within results"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="w-full px-3 py-2 bg-[#141E2D] border border-zinc-700 rounded text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500 mb-4"
            />
            <div className="flex-1 min-h-0 overflow-y-auto space-y-2">
            {loading ? (
              <div className="text-center text-zinc-500 py-8">Loading...</div>
            ) : error ? (
              <div className="text-center text-red-500 py-8">{error}</div>
            ) : filteredPapers.length === 0 ? (
              <div className="text-center text-zinc-500 py-8">
                No papers found
              </div>
            ) : (
              filteredPapers.map((paper) => (
                <PaperCard
                  key={paper.id}
                  paper={paper}
                  isSelected={selectedPaper?.id === paper.id}
                  onClick={() => {
                    setSelectedPaper(paper);
                    // Scroll preview panel to top when paper is selected
                    previewScrollRef.current?.scrollTo({
                      top: 0,
                      behavior: "smooth",
                    });
                  }}
                />
              ))
            )}
            </div>
          </div>
        </aside>

        {/* Right Panel - Preview */}
        <section className="flex-1 flex flex-col">
          {/* Preview Container Box */}
          <div
            ref={previewScrollRef}
            className="flex-1 min-h-0 overflow-y-auto p-6 bg-[#101723] rounded-lg"
          >
            <PaperPreview paper={selectedPaper} />
          </div>
        </section>
      </main>
    </div>
  );
}
