export function relevanceColor(score: number): string {
  if (score >= 0.8) return "#10b981";
  if (score >= 0.7) return "#84cc16";
  if (score >= 0.6) return "#eab308";
  if (score >= 0.5) return "#f59e0b";
  if (score >= 0.4) return "#f97316";
  if (score >= 0.3) return "#ef4444";
  return "#dc2626";
}
