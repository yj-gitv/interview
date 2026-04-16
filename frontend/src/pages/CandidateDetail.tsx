import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Candidate, MatchScore, QuestionSet, Interview } from "../api/client";
import ScoreBadge from "../components/ScoreBadge";

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [match, setMatch] = useState<MatchScore | null>(null);
  const [questions, setQuestions] = useState<QuestionSet | null>(null);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [scoring, setScoring] = useState(false);
  const [generatingQ, setGeneratingQ] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    const cid = Number(id);
    const cand = await api.candidates.get(cid);
    setCandidate(cand);
    api.interviews.list(cid).then(setInterviews).catch(() => setInterviews([]));
    try {
      const m = await api.matches.get(cid);
      setMatch(m);
      if (m.questions && m.questions !== "[]") {
        setQuestions(JSON.parse(m.questions));
      } else {
        setQuestions(null);
      }
    } catch {
      setMatch(null);
      setQuestions(null);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleScore = async () => {
    if (!id) return;
    setScoring(true);
    try {
      const m = await api.matches.score(Number(id));
      setMatch(m);
    } finally {
      setScoring(false);
    }
  };

  const handleGenerateQuestions = async () => {
    if (!id) return;
    setGeneratingQ(true);
    try {
      const qs = await api.matches.generateQuestions(Number(id));
      setQuestions(qs);
    } finally {
      setGeneratingQ(false);
    }
  };

  if (!candidate) {
    return <div className="text-gray-500">加载中...</div>;
  }

  const recLabel: Record<string, string> = {
    推荐: "bg-green-100 text-green-800 border-green-200",
    待定: "bg-yellow-100 text-yellow-800 border-yellow-200",
    不推荐: "bg-red-100 text-red-800 border-red-200",
  };

  const sectionLabels: Record<string, string> = {
    opening: "开场问题",
    experience_verification: "经历验证",
    competency: "能力考察",
    risk_probing: "风险探测",
    culture_fit: "文化匹配",
  };

  return (
    <div>
      <Link
        to={`/positions/${candidate.position_id}`}
        className="text-sm text-blue-600 hover:text-blue-800"
      >
        &larr; 返回岗位
      </Link>
      <h2 className="text-xl font-bold text-gray-900 mt-2">
        {candidate.display_name || candidate.codename}
      </h2>

      {/* Match Scores */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">匹配评分</h3>
          <button
            onClick={handleScore}
            disabled={scoring}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
          >
            {scoring ? "评分中..." : match ? "重新评分" : "开始评分"}
          </button>
        </div>

        {match ? (
          <div>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
              <ScoreBadge
                score={match.experience_score}
                label="岗位经验"
                note={match.experience_note}
              />
              <ScoreBadge
                score={match.industry_score}
                label="行业背景"
                note={match.industry_note}
              />
              <ScoreBadge
                score={match.competency_score}
                label="核心能力"
                note={match.competency_note}
              />
              <ScoreBadge
                score={match.potential_score}
                label="成长潜力"
                note={match.potential_note}
              />
              <ScoreBadge
                score={match.overall_score}
                label="综合推荐"
                note={match.recommendation}
              />
            </div>

            <div className="flex items-center gap-2 mb-4">
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold border ${recLabel[match.recommendation] || "bg-gray-100"}`}
              >
                {match.recommendation}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">亮点</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  {JSON.parse(match.highlights || "[]").map(
                    (h: string, i: number) => (
                      <li key={i}>• {h}</li>
                    )
                  )}
                </ul>
              </div>
              <div className="bg-red-50 rounded-lg p-4">
                <h4 className="font-medium text-red-800 mb-2">风险点</h4>
                <ul className="text-sm text-red-700 space-y-1">
                  {JSON.parse(match.risks || "[]").map(
                    (r: string, i: number) => (
                      <li key={i}>• {r}</li>
                    )
                  )}
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-500">
            点击「开始评分」进行简历-JD匹配分析
          </div>
        )}
      </div>

      {/* Interview Questions */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">面试问题</h3>
          <button
            onClick={handleGenerateQuestions}
            disabled={generatingQ || !match}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
          >
            {generatingQ
              ? "生成中..."
              : questions
                ? "重新生成"
                : "生成问题"}
          </button>
        </div>

        {questions ? (
          <div className="space-y-6">
            {Object.entries(questions).map(([section, items]) => {
              if (!items || items.length === 0) return null;
              return (
                <div key={section}>
                  <h4 className="font-medium text-gray-800 mb-2">
                    {sectionLabels[section] || section}
                  </h4>
                  <div className="space-y-3">
                    {items.map(
                      (
                        q: {
                          question: string;
                          purpose: string;
                          good_answer_elements: string[];
                          red_flags: string[];
                        },
                        i: number
                      ) => (
                        <div
                          key={i}
                          className="bg-white border border-gray-200 rounded-lg p-4"
                        >
                          <p className="font-medium text-gray-900">
                            {q.question}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            考察目的：{q.purpose}
                          </p>
                          {q.good_answer_elements.length > 0 && (
                            <div className="mt-2">
                              <span className="text-xs text-green-600 font-medium">
                                优秀回答要素：
                              </span>
                              <span className="text-xs text-green-600">
                                {q.good_answer_elements.join("、")}
                              </span>
                            </div>
                          )}
                          {q.red_flags.length > 0 && (
                            <div className="mt-1">
                              <span className="text-xs text-red-600 font-medium">
                                红旗信号：
                              </span>
                              <span className="text-xs text-red-600">
                                {q.red_flags.join("、")}
                              </span>
                            </div>
                          )}
                        </div>
                      )
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-500">
            {match
              ? "点击「生成问题」创建面试问题清单"
              : "请先完成匹配评分，再生成面试问题"}
          </div>
        )}
      </div>

      {/* Interviews */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">
            面试记录 {interviews.length > 0 && <span className="text-gray-400 font-normal text-sm">({interviews.length})</span>}
          </h3>
          <button
            onClick={async () => {
              if (!id || !match) return;
              const questionsJson = match.questions || "[]";
              const iv = await api.interviews.create({
                position_id: candidate!.position_id,
                candidate_id: Number(id),
                questions_json: questionsJson,
              });
              window.location.href = `/interviews/${iv.id}/live`;
            }}
            disabled={!match}
            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors"
          >
            新建面试
          </button>
        </div>

        {interviews.length > 0 ? (
          <div className="space-y-2">
            {interviews.map((iv) => {
              const statusMap: Record<string, { label: string; cls: string }> = {
                scheduled: { label: "待开始", cls: "bg-gray-100 text-gray-600" },
                in_progress: { label: "进行中", cls: "bg-blue-100 text-blue-700 animate-pulse" },
                completed: { label: "已完成", cls: "bg-green-100 text-green-700" },
                cancelled: { label: "已取消", cls: "bg-red-100 text-red-600" },
              };
              const st = statusMap[iv.status] || statusMap.scheduled;
              const date = iv.started_at
                ? new Date(iv.started_at).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })
                : new Date(iv.created_at).toLocaleDateString("zh-CN");
              const dur = iv.duration_seconds > 0 ? `${Math.round(iv.duration_seconds / 60)} 分钟` : "";

              return (
                <div key={iv.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${st.cls}`}>
                      {st.label}
                    </span>
                    <span className="text-sm text-gray-700">{date}</span>
                    {dur && <span className="text-xs text-gray-400">{dur}</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    {iv.status === "in_progress" && (
                      <Link
                        to={`/interviews/${iv.id}/live`}
                        className="text-xs px-2.5 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                      >
                        进入面试
                      </Link>
                    )}
                    {iv.status === "completed" && (
                      <Link
                        to={`/interviews/${iv.id}/summary`}
                        className="text-xs px-2.5 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                      >
                        {iv.has_summary ? "查看总结" : "生成总结"}
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl p-6 text-center text-gray-500 text-sm">
            {match ? "点击「新建面试」开始" : "请先完成匹配评分"}
          </div>
        )}
      </div>
    </div>
  );
}
