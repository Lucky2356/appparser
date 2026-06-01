export function ScoreBadge({ score }: { score: number }) {
  const tone =
    score >= 82
      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
      : score >= 68
        ? "bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200"
        : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200";

  return (
    <div className={`inline-flex h-9 items-center rounded-md px-3 text-sm font-semibold ${tone}`}>
      {Math.round(score)}
    </div>
  );
}
