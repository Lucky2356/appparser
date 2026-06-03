export function ScoreBadge({ score }: { score: number }) {
  const rounded = Math.round(score);
  const tone =
    score >= 82
      ? "bg-emerald-50 text-emerald-800 ring-emerald-200 dark:bg-emerald-950 dark:text-emerald-200 dark:ring-emerald-900"
      : score >= 68
        ? "bg-cyan-50 text-cyan-800 ring-cyan-200 dark:bg-cyan-950 dark:text-cyan-200 dark:ring-cyan-900"
        : "bg-amber-50 text-amber-800 ring-amber-200 dark:bg-amber-950 dark:text-amber-200 dark:ring-amber-900";

  return (
    <div className={`w-24 rounded-md px-3 py-2 text-right ring-1 ${tone}`}>
      <div className="text-xs font-medium opacity-75">скор</div>
      <div className="text-xl font-bold leading-5">{rounded}</div>
    </div>
  );
}
