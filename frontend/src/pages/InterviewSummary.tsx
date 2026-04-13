import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Interview, InterviewSummary as SummaryType } from "../api/client";
import ScoreBadge from "../components/ScoreBadge";

export default function InterviewSummary() {
  const { id } = useParams<{ id: string }>();
  const [interview, setInterview] = useState<Interview | null>(null);
  const [summary, setSummary] = useState<SummaryType | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!id) return;
    const iid = Number(id);
    api.interviews.get(iid).then(setInterview);
    api.summaries.get(iid).then(setSummary).catch(() => setSummary(null));
  }, [id]);

  const handleGenerate = async () => {
    if (!id) return;
    setGenerating(true);
    try {
      const s = await api.summaries.generate(Number(id));
      setSummary(s);
    } finally {
      setGenerating(false);
    }
  };

  const handleExportPdf = () => {
    if (!id) return;
    window.open(api.summaries.exportPdf(Number(id)), "_blank");
  };

  if (!interview) return <div className="text-gray-500">Loading...</div>;

  const recStyle: Record<string, string> = {
    推荐: "bg-green-100 text-green-800 border-green-200",
    待定: "bg-yellow-100 text-yellow-800 border-yellow-200",
    不推荐: "bg-red-100 text-red-800 border-red-200",
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link
            to={`/candidates/${interview.candidate_id}`}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            &larr; 返回候选人
          </Link>
          <h2 className="text-xl font-bold text-gray-900 mt-2">
            面试总结 — {interview.candidate_codename}
          </h2>
          <p className="text-sm text-gray-500">
            {interview.position_title} |{" "}
            {interview.duration_seconds > 0
              ? `${Math.round(interview.duration_seconds / 60)} 分钟`
              : "N/A"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
          >
            {generating ? "生成中..." : summary ? "重新生成" : "生成总结"}
          </button>
          {summary && (
            <>
              <button
                onClick={handleExportPdf}
                className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700"
              >
                导出 PDF
              </button>
              <button
                onClick={async () => {
                  if (!id) return;
                  const result = await api.summaries.push(Number(id));
                  alert(
                    result.pushed.dingtalk || result.pushed.feishu
                      ? "推送成功"
                      : "未配置推送渠道"
                  );
                }}
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700"
              >
                推送结果
              </button>
            </>
          )}
        </div>
      </div>

      {summary ? (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <span
              className={`px-4 py-1.5 rounded-full text-sm font-semibold border ${
                recStyle[summary.recommendation] || "bg-gray-100"
              }`}
            >
              {summary.recommendation}
            </span>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-2">候选人概要</h3>
            <p className="text-sm text-gray-700">{summary.candidate_overview}</p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
            <ScoreBadge score={summary.expression_score} label="表达清晰度" />
            <ScoreBadge score={summary.case_richness_score} label="案例丰富度" />
            <ScoreBadge score={summary.depth_score} label="思维深度" />
            <ScoreBadge score={summary.self_awareness_score} label="自我认知" />
            <ScoreBadge score={summary.enthusiasm_score} label="岗位热情" />
            <ScoreBadge score={summary.overall_score} label="综合评分" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-green-50 rounded-lg p-4">
              <h4 className="font-medium text-green-800 mb-2">亮点</h4>
              <ul className="text-sm text-green-700 space-y-1">
                {JSON.parse(summary.highlights || "[]").map(
                  (h: string, i: number) => (
                    <li key={i}>• {h}</li>
                  )
                )}
              </ul>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <h4 className="font-medium text-red-800 mb-2">顾虑点</h4>
              <ul className="text-sm text-red-700 space-y-1">
                {JSON.parse(summary.concerns || "[]").map(
                  (c: string, i: number) => (
                    <li key={i}>• {c}</li>
                  )
                )}
              </ul>
            </div>
          </div>

          {(() => {
            const alignment = JSON.parse(summary.jd_alignment || "[]");
            if (alignment.length === 0) return null;
            const statusColor: Record<string, string> = {
              达成: "text-green-700 bg-green-100",
              部分达成: "text-yellow-700 bg-yellow-100",
              未达成: "text-red-700 bg-red-100",
            };
            return (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3">
                  JD 匹配分析
                </h3>
                <div className="space-y-2">
                  {alignment.map(
                    (
                      item: { requirement: string; status: string; note: string },
                      i: number
                    ) => (
                      <div key={i} className="flex items-start gap-3">
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-medium shrink-0 ${
                            statusColor[item.status] ||
                            "text-gray-600 bg-gray-100"
                          }`}
                        >
                          {item.status}
                        </span>
                        <div>
                          <span className="text-sm font-medium text-gray-800">
                            {item.requirement}
                          </span>
                          {item.note && (
                            <span className="text-sm text-gray-500 ml-2">
                              {item.note}
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            );
          })()}

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-2">推荐理由</h3>
            <p className="text-sm text-gray-700">
              {summary.recommendation_reason}
            </p>
          </div>

          {summary.next_steps && (
            <div className="bg-blue-50 rounded-xl border border-blue-200 p-5">
              <h3 className="font-semibold text-blue-900 mb-2">后续建议</h3>
              <p className="text-sm text-blue-700">{summary.next_steps}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center text-gray-500">
          <p className="text-lg mb-2">暂无面试总结</p>
          <p className="text-sm">
            点击「生成总结」基于面试转录自动生成结构化报告
          </p>
        </div>
      )}
    </div>
  );
}
