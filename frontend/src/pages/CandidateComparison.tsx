import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Position, ComparisonEntry } from "../api/client";

function ScoreCell({ score }: { score: number | undefined }) {
  if (score === undefined || score === null) return <td className="px-3 py-2 text-center text-gray-300">—</td>;
  const color =
    score >= 80
      ? "text-green-700 bg-green-50"
      : score >= 60
        ? "text-yellow-700 bg-yellow-50"
        : "text-red-700 bg-red-50";
  return (
    <td className={`px-3 py-2 text-center text-sm font-semibold ${color}`}>
      {score}
    </td>
  );
}

function RecBadge({ rec }: { rec: string | undefined }) {
  if (!rec) return <span className="text-gray-300">—</span>;
  const style: Record<string, string> = {
    "推荐": "bg-green-100 text-green-800",
    "待定": "bg-yellow-100 text-yellow-800",
    "不推荐": "bg-red-100 text-red-800",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${style[rec] || "bg-gray-100 text-gray-600"}`}>
      {rec}
    </span>
  );
}

export default function CandidateComparison() {
  const { id } = useParams<{ id: string }>();
  const [position, setPosition] = useState<Position | null>(null);
  const [entries, setEntries] = useState<ComparisonEntry[]>([]);

  useEffect(() => {
    if (!id) return;
    const pid = Number(id);
    api.positions.get(pid).then(setPosition);
    api.comparison.get(pid).then(setEntries);
  }, [id]);

  if (!position) return <div className="text-gray-500">加载中...</div>;

  const sorted = [...entries].sort(
    (a, b) => (b.match?.overall_score ?? 0) - (a.match?.overall_score ?? 0)
  );

  return (
    <div>
      <div className="mb-6">
        <Link to={`/positions/${id}`} className="text-sm text-blue-600 hover:text-blue-800">
          &larr; 返回岗位
        </Link>
        <h2 className="text-xl font-bold text-gray-900 mt-2">
          候选人对比 — {position.title}
        </h2>
        <p className="text-sm text-gray-500">{entries.length} 位候选人</p>
      </div>

      {entries.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center text-gray-500">
          暂无候选人数据
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full bg-white rounded-xl border border-gray-200 text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-3 py-3 text-left font-semibold text-gray-700">候选人</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700" colSpan={5}>简历匹配</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700">匹配推荐</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700" colSpan={5}>面试评估</th>
                <th className="px-3 py-3 text-center font-semibold text-gray-700">面试推荐</th>
              </tr>
              <tr className="border-b border-gray-100 bg-gray-50/50 text-xs text-gray-500">
                <th className="px-3 py-1"></th>
                <th className="px-3 py-1 text-center">经验</th>
                <th className="px-3 py-1 text-center">行业</th>
                <th className="px-3 py-1 text-center">能力</th>
                <th className="px-3 py-1 text-center">潜力</th>
                <th className="px-3 py-1 text-center">综合</th>
                <th className="px-3 py-1"></th>
                <th className="px-3 py-1 text-center">表达</th>
                <th className="px-3 py-1 text-center">案例</th>
                <th className="px-3 py-1 text-center">深度</th>
                <th className="px-3 py-1 text-center">认知</th>
                <th className="px-3 py-1 text-center">综合</th>
                <th className="px-3 py-1"></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((e, i) => (
                <tr key={e.candidate_id} className={`border-b border-gray-100 ${i === 0 ? "bg-blue-50/30" : "hover:bg-gray-50"}`}>
                  <td className="px-3 py-2">
                    <Link to={`/candidates/${e.candidate_id}`} className="font-medium text-blue-600 hover:text-blue-800">
                      {e.display_name || e.codename}
                    </Link>
                  </td>
                  <ScoreCell score={e.match?.experience_score} />
                  <ScoreCell score={e.match?.industry_score} />
                  <ScoreCell score={e.match?.competency_score} />
                  <ScoreCell score={e.match?.potential_score} />
                  <ScoreCell score={e.match?.overall_score} />
                  <td className="px-3 py-2 text-center">
                    <RecBadge rec={e.match?.recommendation} />
                  </td>
                  <ScoreCell score={e.interview_summary?.expression_score} />
                  <ScoreCell score={e.interview_summary?.case_richness_score} />
                  <ScoreCell score={e.interview_summary?.depth_score} />
                  <ScoreCell score={e.interview_summary?.self_awareness_score} />
                  <ScoreCell score={e.interview_summary?.overall_score} />
                  <td className="px-3 py-2 text-center">
                    <RecBadge rec={e.interview_summary?.recommendation} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Highlights / Risks comparison */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sorted.map((e) => (
              <div key={e.candidate_id} className="bg-white rounded-xl border border-gray-200 p-4">
                <h4 className="font-semibold text-gray-900 mb-3">{e.display_name || e.codename}</h4>
                {e.match && (
                  <>
                    {e.match.highlights.length > 0 && (
                      <div className="mb-2">
                        <span className="text-xs font-medium text-green-700">亮点：</span>
                        <ul className="text-xs text-green-600 mt-1 space-y-0.5">
                          {e.match.highlights.map((h, j) => <li key={j}>+ {h}</li>)}
                        </ul>
                      </div>
                    )}
                    {e.match.risks.length > 0 && (
                      <div>
                        <span className="text-xs font-medium text-red-700">风险：</span>
                        <ul className="text-xs text-red-600 mt-1 space-y-0.5">
                          {e.match.risks.map((r, j) => <li key={j}>- {r}</li>)}
                        </ul>
                      </div>
                    )}
                  </>
                )}
                {!e.match && <p className="text-xs text-gray-400">未评分</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
