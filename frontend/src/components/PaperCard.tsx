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
      className={`p-4 rounded-lg cursor-pointer transition-colors ${
        isSelected
          ? "bg-zinc-800 border-2 border-purple-500"
          : "bg-zinc-900 border border-zinc-700 hover:bg-zinc-800"
      }`}
    >
      <h3 className="text-white font-medium mb-2 line-clamp-2">
        {paper.title}
      </h3>
      <p className="text-zinc-400 text-sm mb-3">
        {category} • {year} • {citations} cites
      </p>
      <div className="flex gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            // CITES functionality - placeholder
          }}
          className="px-3 py-1 text-xs bg-zinc-800 hover:bg-zinc-700 text-white rounded transition-colors"
        >
          CITES
        </button>
        {paper.pdfUrl && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              window.open(paper.pdfUrl!, "_blank");
            }}
            className="px-3 py-1 text-xs bg-zinc-800 hover:bg-zinc-700 text-white rounded transition-colors"
          >
            OPEN PDF
          </button>
        )}
      </div>
    </div>
  );
}
