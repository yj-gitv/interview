import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Interview, InterviewSummary as SummaryType } from "../api/client";
import ScoreBadge from "../components/ScoreBadge";

type Tab = "performance" | "jd";

export default function InterviewSummary() {
  const { id } = useParams<{ id: string }>();
  const [interview, setInterview] = useState<Interview | null>(null);
  const [summary, setSummary] = useState<SummaryType | null>(null);
  const [generating, setGenerating] = useState(false);
  const [pushing, setPushing] = useState(false);
  const [tab, setTab] = useState<Tab>("performance");

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

  const tabCls = (t: Tab) =>
    `px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
      tab === t
        ? "border-blue-600 text-blue-600"
        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
    }`;

  const alignment = summary ? JSON.parse(summary.jd_alignment || "[]") : [];
  const statusColor: Record<string, string> = {
    达成: "text-green-700 bg-green-100",
    部分达成: "text-yellow-700 bg-yellow-100",
    未达成: "text-red-700 bg-red-100",
  };

  const jdStats = alignment.reduce(
    (acc: Record<string, number>, item: { status: string }) => {
      acc[item.status] = (acc[item.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

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
            面试总结 — {interview.candidate_display_name || interview.candidate_codename}
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
                  setPushing(true);
                  try {
                    const result = await api.summaries.push(Number(id));
                    if (result.pushed.dingtalk || result.pushed.feishu) {
                      alert(
                        `推送成功！\n钉钉: ${result.pushed.dingtalk ? "✓" : "未配置"}\n飞书: ${result.pushed.feishu ? "✓" : "未配置"}`
                      );
                    } else {
                      alert(
                        "未配置推送渠道。\n\n请在 .env 文件中设置：\n• INTERVIEW_DINGTALK_WEBHOOK_URL\n• INTERVIEW_FEISHU_WEBHOOK_URL\n\n或前往「系统设置」页查看配置说明。"
                      );
                    }
                  } catch (e) {
                    alert(`推送失败: ${e instanceof Error ? e.message : "未知错误"}`);
                  } finally {
                    setPushing(false);
                  }
                }}
                disabled={pushing}
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:bg-gray-300"
              >
                {pushing ? "推送中..." : "推送结果"}
              </button>
            </>
          )}
        </div>
      </div>

      {summary ? (
        <div className="space-y-6">
          {/* Recommendation + Overview */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-3 mb-3">
              <span
                className={`px-4 py-1.5 rounded-full text-sm font-semibold border ${
                  recStyle[summary.recommendation] || "bg-gray-100"
                }`}
              >
                {summary.recommendation}
              </span>
            </div>
            <p className="text-sm text-gray-700">{summary.candidate_overview}</p>
            {summary.recommendation_reason && (
              <p className="text-sm text-gray-500 mt-2 pt-2 border-t border-gray-100">
                {summary.recommendation_reason}
              </p>
            )}
          </div>

          {/* Tab bar */}
          <div className="border-b border-gray-200">
            <nav className="flex gap-0 -mb-px">
              <button className={tabCls("performance")} onClick={() => setTab("performance")}>
                面试表现
              </button>
              <button className={tabCls("jd")} onClick={() => setTab("jd")}>
                JD 匹配分析
                {alignment.length > 0 && (
                  <span className="ml-1.5 text-xs text-gray-400">
                    ({alignment.length})
                  </span>
                )}
              </button>
            </nav>
          </div>

          {/* Tab: Performance */}
          {tab === "performance" && (
            <div className="space-y-5">
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

              {summary.next_steps && (
                <div className="bg-blue-50 rounded-xl border border-blue-200 p-5">
                  <h3 className="font-semibold text-blue-900 mb-2">后续建议</h3>
                  <p className="text-sm text-blue-700">{summary.next_steps}</p>
                </div>
              )}
            </div>
          )}

          {/* Tab: JD Alignment */}
          {tab === "jd" && (
            <div className="space-y-5">
              {alignment.length > 0 && (
                <div className="flex gap-3">
                  {(["达成", "部分达成", "未达成"] as const).map((s) =>
                    jdStats[s] ? (
                      <span
                        key={s}
                        className={`text-xs px-2.5 py-1 rounded-full font-medium ${statusColor[s] || "bg-gray-100 text-gray-600"}`}
                      >
                        {s} {jdStats[s]}
                      </span>
                    ) : null,
                  )}
                </div>
              )}

              {alignment.length > 0 ? (
                <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
                  {alignment.map(
                    (
                      item: { requirement: string; status: string; note: string },
                      i: number
                    ) => (
                      <div key={i} className="flex items-start gap-3 px-5 py-3">
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-medium shrink-0 mt-0.5 ${
                            statusColor[item.status] ||
                            "text-gray-600 bg-gray-100"
                          }`}
                        >
                          {item.status}
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-gray-800">
                            {item.requirement}
                          </p>
                          {item.note && (
                            <p className="text-sm text-gray-500 mt-0.5">
                              {item.note}
                            </p>
                          )}
                        </div>
                      </div>
                    )
                  )}
                </div>
              ) : (
                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-400">
                  暂无 JD 匹配分析数据
                </div>
              )}
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
