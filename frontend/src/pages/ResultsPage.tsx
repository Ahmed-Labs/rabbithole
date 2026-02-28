import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import rabbitLogo from "../assets/rabbit-logo.png";
import type { Paper } from "../types/Paper";
import { PaperCard } from "../components/PaperCard";
import { PaperPreview } from "../components/PaperPreview";

export function ResultsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const searchQuery = searchParams.get("q") ?? "";

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
        const response = await fetch(
          `/api/search?query=${encodeURIComponent(searchQuery)}`,
        );
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.error || `Failed to search papers (${response.status})`,
          );
        }
        const data = await response.json();
        const list = (data.papers ?? []).map(mapPaper);
        setPapers(list);
        if (list.length > 0) setSelectedPaper(list[0]);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unknown error occurred. Make sure the Flask backend is running on port 5000.",
        );
      } finally {
        setLoading(false);
      }
    };

    fetchPapers();
  }, [searchQuery]);

  const handleAnalyze = (paperId: string, depth: number) => {
    navigate(`/flow?paperId=${paperId}&depth=${depth}`);
  };

  const filteredPapers = papers.filter((paper) =>
    paper.title.toLowerCase().includes(filterQuery.toLowerCase()),
  );

  return (
    <div className="min-h-screen bg-page-bg text-text flex flex-col">
      <div className="px-6 pt-6">
        <header className="flex items-center justify-between px-6 py-4 bg-panel-bg rounded-lg">
          <div className="flex items-center gap-1 text-2xl font-semibold">
            RabbitHole
            <img src={rabbitLogo} alt="Logo" className="h-6 w-auto" />
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="px-4 py-2 text-sm border border-zinc-600 rounded-lg bg-transparent text-text cursor-pointer hover:bg-zinc-800 transition-colors"
            >
              New search
            </button>
            <button
              type="button"
              className="px-4 py-2 text-sm border border-zinc-600 rounded-lg bg-transparent text-text cursor-pointer hover:bg-zinc-800 transition-colors"
            >
              Settings
            </button>
          </div>
        </header>
      </div>

      <main className="flex-1 min-h-0 flex overflow-hidden p-6 gap-6 items-stretch">
        <aside className="w-1/3 flex flex-col min-h-0">
          <div className="flex-1 min-h-0 flex flex-col bg-input-bg-dark rounded-lg p-4">
            <h2 className="text-lg font-semibold text-text mb-3">Results</h2>
            <input
              type="text"
              placeholder="Search within results"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="w-full px-3 py-2 bg-panel-bg border border-border-default rounded text-text placeholder:text-placeholder mb-4 focus:outline-none focus:ring-2 focus:ring-focus"
            />
            <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-2">
              {loading ? (
                <div className="text-center py-8 text-placeholder">Loading...</div>
              ) : error ? (
                <div className="text-center py-8 text-danger">{error}</div>
              ) : filteredPapers.length === 0 ? (
                <div className="text-center py-8 text-placeholder">
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

        <section className="flex-1 flex flex-col min-h-0">
          <div
            ref={previewScrollRef}
            className="flex-1 min-h-0 overflow-y-auto p-6 bg-input-bg-dark rounded-lg"
          >
            <PaperPreview paper={selectedPaper} onAnalyze={handleAnalyze} />
          </div>
        </section>
      </main>
    </div>
  );
}
