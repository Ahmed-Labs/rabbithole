export interface FlowFilters {
  searchQuery: string;
  searchEnabled: boolean;
  yearMin: number;
  yearMax: number;
  yearEnabled: boolean;
  minCitations: number;
  citationsEnabled: boolean;
  minRelevance: number;
  similarityEnabled: boolean;
}

/** Semantic Scholar corpus includes papers from the 20th century onward; 1900 is a safe lower bound. */
const YEAR_MIN = 1900;
const CITATIONS_MAX = 225000;
const CITATIONS_LOW_RANGE = 1000; // most of the slider covers 0–1000
const SLIDER_BREAK = 0.9; // last 10% of slider covers 1000–225000
const RELEVANCE_STEP = 0.01;

/** Map citation count to slider position (0–1). Most of slider is 0–1000; right edge is 1000–225000. */
function citationToSlider(value: number): number {
  if (value <= 0) return 0;
  if (value <= CITATIONS_LOW_RANGE) {
    return (value / CITATIONS_LOW_RANGE) * SLIDER_BREAK;
  }
  return (
    SLIDER_BREAK +
    ((value - CITATIONS_LOW_RANGE) / (CITATIONS_MAX - CITATIONS_LOW_RANGE)) *
      (1 - SLIDER_BREAK)
  );
}

/** Map slider position (0–1) to citation count. */
function sliderToCitation(slider: number): number {
  if (slider <= 0) return 0;
  if (slider <= SLIDER_BREAK) {
    return Math.round((slider / SLIDER_BREAK) * CITATIONS_LOW_RANGE);
  }
  return Math.round(
    CITATIONS_LOW_RANGE +
      ((slider - SLIDER_BREAK) / (1 - SLIDER_BREAK)) *
        (CITATIONS_MAX - CITATIONS_LOW_RANGE),
  );
}

interface FilterSidebarProps {
  filters: FlowFilters;
  onFiltersChange: (filters: FlowFilters) => void;
  onReset?: () => void;
}

export function FilterSidebar({
  filters,
  onFiltersChange,
  onReset,
}: FilterSidebarProps) {
  const yearMax = new Date().getFullYear();

  const update = (patch: Partial<FlowFilters>) => {
    onFiltersChange({ ...filters, ...patch });
  };

  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl bg-panel-bg border border-border-default">
      <div className="px-3 py-3 border-b border-border-default flex items-center justify-between gap-2">
        <div className="text-sm font-medium text-text">Filters</div>
        {onReset ? (
          <button
            type="button"
            onClick={onReset}
            className="cursor-pointer text-xs text-text-muted hover:text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus rounded px-2 py-1"
          >
            Reset filters
          </button>
        ) : null}
      </div>

      <div className="flex flex-1 min-h-0 flex-col gap-4 overflow-y-auto px-3 py-3">
        {/* Relevance — score displayed as percentage */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between gap-2">
            <label
              htmlFor="flow-filter-relevance-cb"
              className="text-sm text-text cursor-pointer"
            >
              Relevance
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() =>
                  update({ minRelevance: 0, similarityEnabled: false })
                }
                className="cursor-pointer text-xs text-text-muted hover:text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus rounded px-1.5 py-0.5"
                aria-label="Reset relevance filter"
              >
                Reset
              </button>
              <input
                id="flow-filter-relevance-cb"
                type="checkbox"
                checked={filters.similarityEnabled}
                onChange={(e) =>
                  update({ similarityEnabled: e.target.checked })
                }
                aria-label="Enable relevance filter"
                className="cursor-pointer h-4 w-4 rounded border-border-default accent-primary"
              />
            </div>
          </div>
          <div
            className={`flex flex-col gap-2.5 transition-opacity ${!filters.similarityEnabled ? "opacity-50 pointer-events-none" : ""}`}
          >
          <p className="text-xs text-text-muted">
            Relevance score: type a percentage (0–100) or use the slider below.
          </p>
          <div
            className="
              flex items-center gap-2 rounded-2xl border border-border-default
              bg-input-bg px-3 py-2 focus-within:ring-1 focus-within:ring-focus/30
            "
          >
            <input
              id="flow-filter-similarity-input"
              type="number"
              min={0}
              max={100}
              step={1}
              value={Math.round(filters.minRelevance * 100)}
              onChange={(e) => {
                const v = Number(e.target.value);
                if (!Number.isNaN(v))
                  update({
                    minRelevance: Math.max(
                      0,
                      Math.min(1, v / 100),
                    ),
                  });
              }}
              aria-label="Minimum relevance score as percentage (type or use slider)"
              className="min-w-0 flex-1 bg-transparent text-text tabular-nums outline-none"
            />
            <span className="shrink-0 text-text-muted">%</span>
          </div>
          <input
            id="flow-filter-similarity"
            type="range"
            min={0}
            max={1}
            step={RELEVANCE_STEP}
            value={filters.minRelevance}
            onChange={(e) =>
              update({ minRelevance: Number(e.target.value) })
            }
            aria-label="Minimum relevance score slider (percentage)"
            className="range-input w-full"
          />
          <div className="text-xs text-text-muted tabular-nums">
            ≥ {Math.round(filters.minRelevance * 100)}% relevance score (slider)
          </div>
          </div>
        </div>

        {/* Year range */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between gap-2">
            <label
              htmlFor="flow-filter-year-cb"
              className="text-sm text-text cursor-pointer"
            >
              Year range
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() =>
                  update({
                    yearMin: YEAR_MIN,
                    yearMax,
                    yearEnabled: false,
                  })
                }
                className="cursor-pointer text-xs text-text-muted hover:text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus rounded px-1.5 py-0.5"
                aria-label="Reset year range filter"
              >
                Reset
              </button>
              <input
                id="flow-filter-year-cb"
                type="checkbox"
                checked={filters.yearEnabled}
                onChange={(e) => update({ yearEnabled: e.target.checked })}
                aria-label="Enable year range filter"
                className="cursor-pointer h-4 w-4 rounded border-border-default accent-primary"
              />
            </div>
          </div>
          <div
            className={`flex flex-col gap-2.5 transition-opacity ${!filters.yearEnabled ? "opacity-50 pointer-events-none" : ""}`}
          >
          <p className="text-xs text-text-muted">
            Type a value or use the sliders below.
          </p>
          <div className="flex items-center gap-2">
            <div
              className="
                flex-1 rounded-2xl border border-border-default bg-input-bg
                px-3 py-2 focus-within:ring-1 focus-within:ring-focus/30
              "
            >
              <label htmlFor="flow-filter-year-min" className="sr-only">
                Minimum year
              </label>
              <input
                id="flow-filter-year-min"
                type="number"
                min={YEAR_MIN}
                max={yearMax}
                value={filters.yearMin}
                onChange={(e) => {
                  const v = Math.round(Number(e.target.value));
                  if (!Number.isNaN(v))
                    update({
                      yearMin: Math.max(YEAR_MIN, Math.min(yearMax, v)),
                      yearMax: Math.max(
                        filters.yearMax,
                        Math.max(YEAR_MIN, Math.min(yearMax, v)),
                      ),
                    });
                }}
                aria-label="Minimum year (type or use slider)"
                className="w-full bg-transparent text-text tabular-nums outline-none"
              />
            </div>
            <span className="text-xs text-text-muted">—</span>
            <div
              className="
                flex-1 rounded-2xl border border-border-default bg-input-bg
                px-3 py-2 focus-within:ring-1 focus-within:ring-focus/30
              "
            >
              <label htmlFor="flow-filter-year-max" className="sr-only">
                Maximum year
              </label>
              <input
                id="flow-filter-year-max"
                type="number"
                min={YEAR_MIN}
                max={yearMax}
                value={filters.yearMax}
                onChange={(e) => {
                  const v = Math.round(Number(e.target.value));
                  if (!Number.isNaN(v))
                    update({
                      yearMax: Math.max(YEAR_MIN, Math.min(yearMax, v)),
                      yearMin: Math.min(
                        filters.yearMin,
                        Math.max(YEAR_MIN, Math.min(yearMax, v)),
                      ),
                    });
                }}
                aria-label="Maximum year (type or use slider)"
                className="w-full bg-transparent text-text tabular-nums outline-none"
              />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <input
              type="range"
              min={YEAR_MIN}
              max={yearMax}
              value={filters.yearMin}
              onChange={(e) => {
                const v = Number(e.target.value);
                update({
                  yearMin: v,
                  yearMax: Math.max(v, filters.yearMax),
                });
              }}
              aria-label="Minimum year slider"
              className="range-input w-full"
            />
            <input
              type="range"
              min={YEAR_MIN}
              max={yearMax}
              value={filters.yearMax}
              onChange={(e) => {
                const v = Number(e.target.value);
                update({
                  yearMax: v,
                  yearMin: Math.min(v, filters.yearMin),
                });
              }}
              aria-label="Maximum year slider"
              className="range-input w-full"
            />
          </div>
          <div className="text-xs text-text-muted tabular-nums">
            {filters.yearMin} — {filters.yearMax} (slider)
          </div>
          </div>
        </div>

        {/* Citations */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between gap-2">
            <label
              htmlFor="flow-filter-citations-cb"
              className="text-sm text-text cursor-pointer"
            >
              Citations
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() =>
                  update({ minCitations: 0, citationsEnabled: false })
                }
                className="cursor-pointer text-xs text-text-muted hover:text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus rounded px-1.5 py-0.5"
                aria-label="Reset citations filter"
              >
                Reset
              </button>
              <input
                id="flow-filter-citations-cb"
                type="checkbox"
                checked={filters.citationsEnabled}
                onChange={(e) =>
                  update({ citationsEnabled: e.target.checked })
                }
                aria-label="Enable citations filter"
                className="cursor-pointer h-4 w-4 rounded border-border-default accent-primary"
              />
            </div>
          </div>
          <div
            className={`flex flex-col gap-2.5 transition-opacity ${!filters.citationsEnabled ? "opacity-50 pointer-events-none" : ""}`}
          >
          <p className="text-xs text-text-muted">
            Type a value or use the slider below.
          </p>
          <div
            className="
              rounded-2xl border border-border-default bg-input-bg
              px-3 py-2 focus-within:ring-1 focus-within:ring-focus/30
            "
          >
            <input
              id="flow-filter-citations-input"
              type="number"
              min={0}
              max={CITATIONS_MAX}
              value={filters.minCitations}
              onChange={(e) => {
                const v = Math.round(Number(e.target.value));
                if (!Number.isNaN(v))
                  update({
                    minCitations: Math.max(0, Math.min(CITATIONS_MAX, v)),
                  });
              }}
              aria-label="Minimum citations (type or use slider)"
              className="w-full bg-transparent text-text tabular-nums outline-none"
            />
          </div>
          <input
            id="flow-filter-citations"
            type="range"
            min={0}
            max={1}
            step={0.001}
            value={citationToSlider(filters.minCitations)}
            onChange={(e) =>
              update({
                minCitations: sliderToCitation(Number(e.target.value)),
              })
            }
            aria-label="Minimum citations slider (log scale)"
            className="range-input w-full"
          />
          <div className="text-xs text-text-muted tabular-nums">
            ≥ {filters.minCitations} (slider)
          </div>
          </div>
        </div>
      </div>
    </div>
  );
}
