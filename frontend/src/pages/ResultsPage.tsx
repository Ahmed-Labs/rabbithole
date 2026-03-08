import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import type { Paper } from "../types/Paper";
import { PaperCard } from "../components/PaperCard";
import { PaperPreview } from "../components/PaperPreview";
import { AppHeader } from "../components/AppHeader";

export function ResultsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const q = searchParams.get("q") ?? "";

  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [query, setQuery] = useState(q);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const listScrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => setQuery(q), [q]);

  useEffect(() => {
    const mapPaper = (p: {
      id: string;
      title: string;
      authors?: { name: string; authorId?: string }[];
      abstract?: string;
      year?: number | null;
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
          `/api/search?query=${encodeURIComponent(q)}`,
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
        setSelectedId(list.length ? list[0].id : null);
        listScrollRef.current?.scrollTo({ top: 0 });
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unknown error. Make sure the backend is running.",
        );
      } finally {
        setLoading(false);
      }
    };

    fetchPapers();
  }, [q]);

  const selectedPaper = useMemo(
    () => papers.find((p) => p.id === selectedId) ?? null,
    [papers, selectedId],
  );

  const onSearch = () => {
    const trimmed = query.trim();
    if (!trimmed) return;

    if (trimmed === q) return;

    setSelectedId(null);
    navigate(`/results?q=${encodeURIComponent(trimmed)}`);
  };

  const handleFindRelated = (paperId: string, depth: number) => {
    navigate(`/flow?paperId=${paperId}&depth=${depth}`);
  };

  return (
    <div className="h-screen flex flex-col bg-page-bg text-text">
      <AppHeader
        showSearch
        searchValue={query}
        onSearchChange={setQuery}
        onSearchSubmit={onSearch}
      />

      <main className="flex-1 min-h-0 px-6 py-6">
        <div className="h-full min-h-0 flex gap-6">
          {/* Left pane */}
          <aside className="w-90 shrink-0 min-h-0 overflow-hidden rounded-2xl bg-panel-bg border border-border-default flex flex-col">
            <div className="px-4 py-4 border-b border-border-default flex items-center justify-between">
              <div className="text-sm font-medium text-text">Results</div>
              {!loading && !error ? (
                <div className="text-xs text-text-muted tabular-nums">
                  {papers.length}
                </div>
              ) : null}
            </div>

            <div
              ref={listScrollRef}
              className="flex-1 min-h-0 overflow-y-auto px-2 pt-2 pb-6"
            >
              {loading ? (
                <div className="py-12 text-center text-text-muted">
                  Searching…
                </div>
              ) : error ? (
                <div className="py-12 text-center text-danger">{error}</div>
              ) : papers.length === 0 ? (
                <div className="py-12 text-center text-text-muted">
                  No results.
                </div>
              ) : (
                <div className="flex flex-col gap-2 p-1">
                  {papers.map((paper) => (
                    <PaperCard
                      key={paper.id}
                      paper={paper}
                      isSelected={paper.id === selectedId}
                      onClick={() => setSelectedId(paper.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </aside>

          {/* Right pane */}
          <section className="flex-1 min-w-0 min-h-0 overflow-hidden rounded-2xl bg-panel-bg border border-border-default flex flex-col">
            <PaperPreview
              paper={selectedPaper}
              onFindRelated={handleFindRelated}
            />
          </section>
        </div>
      </main>
    </div>
  );
}
