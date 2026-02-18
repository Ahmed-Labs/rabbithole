import { useState } from "react";
import type { Paper } from "../types/Paper";
import "./PaperPreview.css";

interface PaperPreviewProps {
  paper: Paper | null;
}

export function PaperPreview({ paper }: PaperPreviewProps) {
  const [referenceDepth, setReferenceDepth] = useState(2);
  const [includeCitations, setIncludeCitations] = useState(false);

  if (!paper) {
    return (
      <div className="paper-preview__empty">
        Select a paper to view details
      </div>
    );
  }

  return (
    <div className="paper-preview">
      <div className="paper-preview__root">
        <h2 className="paper-preview__section-title">Root paper preview</h2>
        <h3 className="paper-preview__title">{paper.title}</h3>
        <div className="paper-preview__tags">
          <span className="paper-preview__tag">{paper.year || "N/A"}</span>
          <span className="paper-preview__tag">IEEE</span>
          <span className="paper-preview__tag">
            {paper.citationCount} citations
          </span>
        </div>

        <div className="paper-preview__abstract-box">
          <h3 className="paper-preview__abstract-title">Abstract</h3>
          <p className="paper-preview__abstract-text">
            {paper.abstract || "No abstract available."}
          </p>
        </div>
      </div>

      <div className="paper-preview__options">
        <h2 className="paper-preview__section-title">Analysis options</h2>
        <div className="paper-preview__options-inner">
          <div>
            <label className="paper-preview__label">Reference depth:</label>
            <input
              type="number"
              min={1}
              max={5}
              value={referenceDepth}
              onChange={(e) => setReferenceDepth(Number(e.target.value))}
              className="paper-preview__input"
            />
          </div>

          <div className="paper-preview__toggle-row">
            <label className="paper-preview__toggle-label">
              Include papers that cite this paper
            </label>
            <button
              type="button"
              onClick={() => setIncludeCitations(!includeCitations)}
              className={`paper-preview__toggle ${
                includeCitations ? "paper-preview__toggle--on" : ""
              }`}
            >
              <span className="paper-preview__toggle-knob" />
            </button>
          </div>
        </div>
        <div className="paper-preview__analyze-wrap">
          <button type="button" className="paper-preview__analyze-btn">
            Analyze
          </button>
        </div>
      </div>
    </div>
  );
}
