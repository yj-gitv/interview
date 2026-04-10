interface ScoreBadgeProps {
  score: number;
  label: string;
  note?: string;
}

export default function ScoreBadge({ score, label, note }: ScoreBadgeProps) {
  const color =
    score >= 80
      ? "text-green-700 bg-green-50 border-green-200"
      : score >= 60
        ? "text-yellow-700 bg-yellow-50 border-yellow-200"
        : "text-red-700 bg-red-50 border-red-200";

  return (
    <div className={`rounded-lg border p-3 ${color}`}>
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-medium">{label}</span>
        <span className="text-lg font-bold">{score}</span>
      </div>
      {note && <p className="text-xs mt-1 opacity-80">{note}</p>}
    </div>
  );
}
