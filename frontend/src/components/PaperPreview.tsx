import { useState } from "react";
import type { Paper } from "../types/Paper";

interface PaperPreviewProps {
  paper: Paper | null;
  onAnalyze: (paperId: string, depth: number) => void;
}

export function PaperPreview({ paper, onAnalyze }: PaperPreviewProps) {
  const [referenceDepth, setReferenceDepth] = useState(2);
  const [includeCitations, setIncludeCitations] = useState(false);

  if (!paper) {
    return (
      <div className="min-h-[400px] flex items-center justify-center text-placeholder">
        Select a paper to view details
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-text mb-4">
          Root paper preview
        </h2>
        <h3 className="text-xl font-semibold text-text mb-3">{paper.title}</h3>

        <div className="flex flex-wrap gap-2 mb-4">
          <span className="px-3 py-1 bg-panel-bg text-text-secondary rounded-full text-sm">
            {paper.year || "N/A"}
          </span>
          <span className="px-3 py-1 bg-panel-bg text-text-secondary rounded-full text-sm">
            IEEE
          </span>
          <span className="px-3 py-1 bg-panel-bg text-text-secondary rounded-full text-sm">
            {paper.citationCount} citations
          </span>
        </div>

        <div className="mb-4 p-4 bg-panel-bg rounded-lg">
          <h3 className="text-text font-medium mb-2">Abstract</h3>
          <p className="text-text-secondary text-sm leading-7">
            {paper.abstract || "No abstract available."}
          </p>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-text mb-4">
          Analysis options
        </h2>

        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-sm text-text-secondary mb-2">
              Reference depth:
            </label>
            <input
              type="number"
              min={1}
              max={5}
              value={referenceDepth}
              onChange={(e) => setReferenceDepth(Number(e.target.value))}
              className="w-full px-3 py-2 bg-panel-bg border border-border-default rounded text-text focus:outline-none focus:ring-2 focus:ring-focus"
            />
          </div>

          <div className="flex items-center justify-between gap-4">
            <label className="text-sm text-text-secondary">
              Include papers that cite this paper
            </label>
            <button
              type="button"
              onClick={() => setIncludeCitations(!includeCitations)}
              className={[
                "relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer",
                includeCitations ? "bg-focus" : "bg-border-default",
              ].join(" ")}
              aria-pressed={includeCitations}
            >
              <span
                className={[
                  "inline-block h-5 w-5 transform rounded-full bg-white transition-transform",
                  includeCitations ? "translate-x-5" : "translate-x-1",
                ].join(" ")}
              />
            </button>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            className="px-8 py-3 bg-primary text-text font-medium rounded-full cursor-pointer hover:bg-primary-hover transition-colors"
            onClick={() => onAnalyze(paper.id, referenceDepth)}
          >
            Analyze
          </button>
        </div>
      </div>
    </div>
  );
}
