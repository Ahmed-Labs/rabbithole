import type { Paper } from "../types/Paper";
import "./PaperCard.css";

interface PaperCardProps {
  paper: Paper;
  isSelected: boolean;
  onClick: () => void;
}

export function PaperCard({ paper, isSelected, onClick }: PaperCardProps) {
  const category = paper.authors[0]?.name || "Unknown";
  const year = paper.year || "N/A";
  const citations = paper.citationCount || 0;

  return (
    <div
      onClick={onClick}
      className={`paper-card ${isSelected ? "paper-card--selected" : ""}`}
    >
      <div className="paper-card__content">
        <h3 className="paper-card__title">{paper.title}</h3>
        <p className="paper-card__meta">
          {category} • {year} • {citations} cites
        </p>
      </div>
      <div className="paper-card__actions">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            // CITES functionality - placeholder
          }}
          className="paper-card__btn"
        >
          CITES
        </button>
        {paper.pdfUrl && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              window.open(paper.pdfUrl!, "_blank");
            }}
            className="paper-card__btn"
          >
            OPEN PDF
          </button>
        )}
      </div>
    </div>
  );
}
