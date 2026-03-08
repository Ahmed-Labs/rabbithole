import { useState } from "react";
import type { Paper } from "../types/Paper";

interface PaperPreviewProps {
  paper: Paper | null;
  onFindRelated: (paperId: string, depth: number) => void;
}

const DEFAULT_DEPTH = 2;
const MAX_DEPTH = 5;

export function PaperPreview({ paper, onFindRelated }: PaperPreviewProps) {
  const [depth, setDepth] = useState(DEFAULT_DEPTH);

  if (!paper) {
    return (
      <div className="h-full min-h-0 flex items-center justify-center text-text-muted">
        Select a paper
      </div>
    );
  }

  const { id, title, year, citationCount, authors, pdfUrl, url, abstract } =
    paper;

  const authorText = authors?.length
    ? authors.map((a) => a.name).join(", ")
    : null;

  return (
    <div className="h-full min-h-0 overflow-y-auto">
      <div className="sticky top-0 z-10 bg-panel-bg/92 backdrop-blur border-b border-border-default">
        <div className="px-6 pt-5 pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="text-xs text-text-muted">
                {year ?? "—"} • {citationCount ?? 0} citations
              </div>

              <h2 className="mt-2 text-lg sm:text-xl font-semibold leading-snug line-clamp-2">
                {title}
              </h2>

              {authorText && (
                <div className="mt-1 text-sm text-text-secondary line-clamp-1">
                  {authorText}
                </div>
              )}
            </div>

            <div className="shrink-0 flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-xl border border-border-default bg-card-bg px-3 py-2">
                <span className="text-xs text-text-muted">Search depth</span>

                <select
                  value={depth}
                  onChange={(e) => setDepth(Number(e.target.value))}
                  className="bg-transparent outline-none text-sm text-text cursor-pointer scheme-dark"
                >
                  {Array.from({ length: MAX_DEPTH }, (_, i) => {
                    const d = i + 1;
                    return (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    );
                  })}
                </select>
              </div>

              <button
                type="button"
                onClick={() => onFindRelated(id, depth)}
                className="
                  cursor-pointer px-4 py-2.5 rounded-xl
                  bg-primary/15 text-primary
                  text-sm font-semibold
                  transition
                  hover:bg-primary/25
                  active:translate-y-[0.5px]
                  focus-visible:ring-2 focus-visible:ring-focus/40
                "
              >
                Find related papers
              </button>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2">
            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className={secondaryBtnClass}
              >
                Open PDF
              </a>
            )}

            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className={secondaryBtnClass}
            >
              View source
            </a>
          </div>
        </div>
      </div>

      <div className="px-6 py-5">
        <div className="text-sm font-medium mb-3">Abstract</div>

        <p className="text-sm text-text-secondary leading-7 whitespace-pre-wrap">
          {abstract || "No abstract available."}
        </p>
      </div>
    </div>
  );
}

const secondaryBtnClass =
  "inline-flex items-center gap-2 cursor-pointer " +
  "px-3 py-2 rounded-xl text-sm font-medium " +
  "bg-card-bg border border-border-default " +
  "text-text-secondary transition " +
  "hover:bg-content-bg/30 hover:text-text hover:border-border-default/80 " +
  "active:translate-y-[0.5px] " +
  "focus-visible:ring-2 focus-visible:ring-focus/35";
