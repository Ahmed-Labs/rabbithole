import { useState } from "react";
import type { Paper } from "../types/Paper";

interface PaperPreviewProps {
  paper: Paper | null;
}

export function PaperPreview({ paper }: PaperPreviewProps) {
  const [referenceDepth, setReferenceDepth] = useState(2);
  const [includeCitations, setIncludeCitations] = useState(false);

  if (!paper) {
    return (
      <div className="flex items-center justify-center text-zinc-500 min-h-[400px]">
        Select a paper to view details
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {/* Root paper preview */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-white mb-4">
          Root paper preview
        </h2>
        <h3 className="text-xl font-semibold text-white mb-3">
          {paper.title}
        </h3>
        <div className="flex gap-2 mb-4">
          <span className="px-3 py-1 bg-[#141E2D] text-zinc-300 rounded-full text-sm">
            {paper.year || "N/A"}
          </span>
          <span className="px-3 py-1 bg-[#141E2D] text-zinc-300 rounded-full text-sm">
            IEEE
          </span>
          <span className="px-3 py-1 bg-[#141E2D] text-zinc-300 rounded-full text-sm">
            {paper.citationCount} citations
          </span>
        </div>

        <div className="mb-4 p-4 bg-[#141E2D] rounded-lg">
          <h3 className="text-white font-medium mb-2">Abstract</h3>
          <p className="text-zinc-300 text-sm leading-relaxed">
            {paper.abstract || "No abstract available."}
          </p>
        </div>
      </div>

      {/* Analysis Options */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          Analysis options
        </h2>
        <div className="space-y-4">
        <div>
          <label className="block text-sm text-zinc-400 mb-2">
            Reference depth:
          </label>
          <input
            type="number"
            min="1"
            max="5"
            value={referenceDepth}
            onChange={(e) => setReferenceDepth(Number(e.target.value))}
            className="w-20 px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-white focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-zinc-300">
            Include papers that cite this paper
          </label>
          <button
            onClick={() => setIncludeCitations(!includeCitations)}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              includeCitations ? "bg-indigo-600" : "bg-zinc-700"
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                includeCitations ? "translate-x-6" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        </div>
        {/* Analyze Button */}
        <div className="pt-4">
          <button className="w-full px-8 py-3 bg-orange-500 hover:bg-orange-400 text-white font-medium rounded-lg transition-colors">
            Analyze
          </button>
        </div>
      </div>
    </div>
  );
}
