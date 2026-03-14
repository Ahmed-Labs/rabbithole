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
const CITATIONS_MAX = 500;
const RELEVANCE_STEP = 0.01;

interface FilterSidebarProps {
  filters: FlowFilters;
  onFiltersChange: (filters: FlowFilters) => void;
}

export function FilterSidebar({ filters, onFiltersChange }: FilterSidebarProps) {
  const yearMax = new Date().getFullYear();

  const update = (patch: Partial<FlowFilters>) => {
    onFiltersChange({ ...filters, ...patch });
  };

  function FilterToggle({
    on,
    onChange,
    ariaLabel,
  }: {
    on: boolean;
    onChange: (on: boolean) => void;
    ariaLabel: string;
  }) {
    return (
      <button
        type="button"
        onClick={() => onChange(!on)}
        aria-label={ariaLabel}
        aria-pressed={on}
        className="cursor-pointer inline-flex rounded-xl border border-border-default bg-input-bg p-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
      >
        <span
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
            on
              ? "bg-primary text-white"
              : "bg-transparent text-text-muted"
          }`}
        >
          On
        </span>
        <span
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
            !on
              ? "bg-primary text-white"
              : "bg-transparent text-text-muted"
          }`}
        >
          Off
        </span>
      </button>
    );
  }

  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl bg-panel-bg border border-border-default">
      <div className="px-4 py-4 border-b border-border-default">
        <div className="text-sm font-medium text-text">Filters</div>
      </div>

      <div className="flex flex-1 min-h-0 flex-col gap-4 overflow-y-auto px-4 py-4">
        {/* Search in graph */}
        <div className="flex flex-col gap-2">
          <label htmlFor="flow-filter-search" className="text-sm text-text">
            Search in graph
          </label>
          <div
            className="
              flex items-center gap-3
              rounded-2xl
              border border-border-default
              bg-input-bg
              px-4 py-3
              transition
              hover:border-border-default/80
              focus-within:ring-1 focus-within:ring-focus/30
            "
          >
            <input
              id="flow-filter-search"
              type="search"
              value={filters.searchQuery}
              onChange={(e) => update({ searchQuery: e.target.value })}
              placeholder="Search in graph…"
              aria-label="Search in graph"
              className="
                w-full bg-transparent outline-none placeholder:text-placeholder
                focus:outline-none focus:ring-0
                focus-visible:outline-none focus-visible:ring-0
                text-text
              "
            />
          </div>
        </div>

        {/* Year range */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm text-text">Year range</span>
            <FilterToggle
              on={filters.yearEnabled}
              onChange={(on) => update({ yearEnabled: on })}
              ariaLabel="Year range filter on or off"
            />
          </div>
          <div
            className={`transition-opacity ${!filters.yearEnabled ? "opacity-50 pointer-events-none" : ""}`}
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
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <label htmlFor="flow-filter-citations-input" className="text-sm text-text">
              Number of Citations
            </label>
            <FilterToggle
              on={filters.citationsEnabled}
              onChange={(on) => update({ citationsEnabled: on })}
              ariaLabel="Citations filter on or off"
            />
          </div>
          <div
            className={`transition-opacity ${!filters.citationsEnabled ? "opacity-50 pointer-events-none" : ""}`}
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
            max={CITATIONS_MAX}
            value={Math.min(filters.minCitations, CITATIONS_MAX)}
            onChange={(e) =>
              update({ minCitations: Number(e.target.value) })
            }
            aria-label="Minimum citations slider"
            className="range-input w-full"
          />
          <div className="text-xs text-text-muted tabular-nums">
            ≥ {filters.minCitations} (slider)
          </div>
          </div>
        </div>

        {/* Relevance — score displayed as percentage */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <label htmlFor="flow-filter-similarity-input" className="text-sm text-text">
              Relevance
            </label>
            <FilterToggle
              on={filters.similarityEnabled}
              onChange={(on) => update({ similarityEnabled: on })}
              ariaLabel="Relevance filter on or off"
            />
          </div>
          <div
            className={`transition-opacity ${!filters.similarityEnabled ? "opacity-50 pointer-events-none" : ""}`}
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
      </div>
    </div>
  );
}
