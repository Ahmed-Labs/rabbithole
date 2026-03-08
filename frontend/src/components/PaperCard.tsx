import type { Paper } from "../types/Paper";

export function PaperCard({
  paper,
  isSelected,
  onClick,
}: {
  paper: Paper;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "w-full text-left rounded-2xl cursor-pointer",
        "px-4 py-3 transition",
        "bg-content-bg/6",
        "hover:bg-content-bg/12",
        "focus-visible:ring-2 focus-visible:ring-focus/40",
        isSelected ? "bg-content-bg/14" : "",
      ].join(" ")}
    >
      <div className="flex items-start gap-3">
        <div
          className={[
            "mt-1 h-8 w-1 rounded-full",
            isSelected ? "bg-primary" : "bg-border-default/40",
          ].join(" ")}
          aria-hidden
        />

        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium leading-snug line-clamp-2">
            {paper.title}
          </div>

          <div className="mt-2 flex items-center gap-2 text-xs text-text-muted">
            <span className="tabular-nums">{paper.year ?? "—"}</span>
            <span className="opacity-50">•</span>
            <span className="tabular-nums">
              {paper.citationCount ?? 0} citations
            </span>
            {paper.pdfUrl ? (
              <>
                <span className="opacity-50">•</span>
                <span>PDF</span>
              </>
            ) : null}
          </div>
        </div>
      </div>
    </button>
  );
}
