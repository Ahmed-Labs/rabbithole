import type { Paper } from "../types/Paper";

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
      className={[
        "p-4 rounded-lg cursor-pointer transition-colors flex items-start justify-between gap-3",
        "bg-card-bg border hover:bg-zinc-800",
        isSelected
          ? "border-2 border-border-accent"
          : "border border-border-default",
      ].join(" ")}
    >
      <div className="flex-1 min-w-0">
        <h3 className="text-text font-medium mb-2 overflow-hidden [display:-webkit-box] [-webkit-line-clamp:2] [-webkit-box-orient:vertical]">
          {paper.title}
        </h3>
        <p className="text-text-muted text-sm">
          {category} • {year} • {citations} cites
        </p>
      </div>
      <div className="flex flex-col gap-2 shrink-0">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            // CITES functionality - placeholder
          }}
          className="px-3 py-1.5 text-xs bg-input-bg-dark text-text rounded cursor-pointer transition-colors whitespace-nowrap hover:bg-[#0d141f]"
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
            className="px-3 py-1.5 text-xs bg-input-bg-dark text-text rounded cursor-pointer transition-colors whitespace-nowrap hover:bg-[#0d141f]"
          >
            OPEN PDF
          </button>
        )}
      </div>
    </div>
  );
}
