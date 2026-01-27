import type { Paper } from "../types/Paper";

interface PaperCardProps {
  paper: Paper;
  isSelected: boolean;
  onClick: () => void;
}

export function PaperCard({ paper, isSelected, onClick }: PaperCardProps) {
  // Extract category from authors or use a default
  const category = paper.authors[0]?.name || "Unknown";
  const year = paper.year || "N/A";
  const citations = paper.citationCount || 0;

  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg cursor-pointer transition-colors flex items-start justify-between gap-3 ${
        isSelected
          ? "bg-[#182436] border-2 border-[#3621F6]"
          : "bg-[#182436] border border-zinc-700 hover:bg-zinc-800"
      }`}
    >
      <div className="flex-1 min-w-0">
        <h3 className="text-white font-medium mb-2 line-clamp-2">
          {paper.title}
        </h3>
        <p className="text-zinc-400 text-sm">
          {category} • {year} • {citations} cites
        </p>
      </div>
      <div className="flex flex-col gap-2 flex-shrink-0">
        <button
          onClick={(e) => {
            e.stopPropagation();
            // CITES functionality - placeholder
          }}
          className="px-3 py-1.5 text-xs bg-[#101723] hover:bg-[#0d141f] text-white rounded transition-colors whitespace-nowrap"
        >
          CITES
        </button>
        {paper.pdfUrl && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              window.open(paper.pdfUrl!, "_blank");
            }}
            className="px-3 py-1.5 text-xs bg-[#101723] hover:bg-[#0d141f] text-white rounded transition-colors whitespace-nowrap"
          >
            OPEN PDF
          </button>
        )}
      </div>
    </div>
  );
}
