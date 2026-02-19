import { useState, useEffect, useRef } from "react";
import rabbitLogo from "../assets/rabbit-logo.png";
import type { Paper } from "../types/Paper";
import { PaperCard } from "../components/PaperCard";
import { PaperPreview, type AnalysisOptions } from "../components/PaperPreview";
import "./ResultsPage.css";

interface ResultsPageProps {
  searchQuery: string;
  onNewSearch: () => void;
  onAnalyze: (options: AnalysisOptions) => void;
}

export function ResultsPage({
  searchQuery,
  onNewSearch,
  onAnalyze,
}: ResultsPageProps) {
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
    <div className="results">
      <div className="results__header-wrap">
        <header className="results__header">
          <div className="results__brand">
            RabbitHole
            <img src={rabbitLogo} alt="Logo" className="results__logo" />
          </div>
          <div className="results__header-actions">
            <button
              type="button"
              onClick={onNewSearch}
              className="results__header-btn"
            >
              New search
            </button>
            <button type="button" className="results__header-btn">
              Settings
            </button>
          </div>
        </header>
      </div>

      <main className="results__main">
        <aside className="results__aside">
          <div className="results__panel">
            <h2 className="results__panel-title">Results</h2>
            <input
              type="text"
              placeholder="Search within results"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="results__filter-input"
            />
            <div className="results__list">
              {loading ? (
                <div className="results__message results__message--muted">
                  Loading...
                </div>
              ) : error ? (
                <div className="results__message results__message--error">
                  {error}
                </div>
              ) : filteredPapers.length === 0 ? (
                <div className="results__message results__message--muted">
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

        <section className="results__preview-section">
          <div ref={previewScrollRef} className="results__preview-scroll">
            <PaperPreview paper={selectedPaper} onAnalyze={onAnalyze} />
          </div>
        </section>
      </main>
    </div>
  );
}
