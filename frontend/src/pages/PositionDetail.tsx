import { useEffect, useState, useCallback, type ChangeEvent } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Position, Candidate, Interview } from "../api/client";

export default function PositionDetail() {
  const { id } = useParams<{ id: string }>();
  const [position, setPosition] = useState<Position | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    const pid = Number(id);
    const [pos, cands] = await Promise.all([
      api.positions.get(pid),
      api.candidates.list(pid),
    ]);
    setPosition(pos);
    setCandidates(cands);
    api.interviews.list(undefined, pid).then(setInterviews).catch(() => setInterviews([]));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // 有未评分候选人时自动轮询刷新（等待后台自动评分完成）
  useEffect(() => {
    const hasPending = candidates.some((c) => !c.has_match);
    if (!hasPending || candidates.length === 0) return;
    const timer = setInterval(() => {
      load();
    }, 3000);
    return () => clearInterval(timer);
  }, [candidates, load]);

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    setUploading(true);
    try {
      await api.candidates.upload(Number(id), file);
      await load();
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  if (!position) {
    return <div className="text-gray-500">加载中...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <Link
          to="/positions"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          &larr; 返回岗位列表
        </Link>
        <h2 className="text-xl font-bold text-gray-900 mt-2">
          {position.title}
        </h2>
        {position.department && (
          <p className="text-sm text-gray-500">{position.department}</p>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <h3 className="font-semibold text-gray-900 mb-2">岗位描述</h3>
        <p className="text-sm text-gray-700 whitespace-pre-wrap">
          {position.jd_text}
        </p>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">
          候选人 ({candidates.length})
        </h3>
        <div className="flex items-center gap-2">
          {candidates.length >= 2 && (
            <Link
              to={`/positions/${id}/compare`}
              className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors"
            >
              对比候选人
            </Link>
          )}
          <label
            className={`px-4 py-2 text-sm font-medium rounded-lg cursor-pointer transition-colors ${
              uploading
                ? "bg-gray-300 text-gray-500"
                : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
          >
            {uploading ? "上传中..." : "上传简历"}
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {candidates.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>暂无候选人</p>
          <p className="text-sm mt-1">上传简历（PDF 或 Word）自动创建候选人</p>
        </div>
      ) : (
        <div className="space-y-3">
          {candidates.map((c) => {
            const civs = interviews.filter((iv) => iv.candidate_id === c.id);
            const latest = civs[0];
            const ivStatus: Record<string, { label: string; cls: string }> = {
              in_progress: { label: "面试中", cls: "bg-blue-100 text-blue-700" },
              completed: { label: "已面试", cls: "bg-purple-100 text-purple-700" },
            };
            const ivBadge = latest ? ivStatus[latest.status] : null;

            return (
              <Link
                key={c.id}
                to={`/candidates/${c.id}`}
                className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">
                      {c.codename}
                    </span>
                    <span className="text-sm text-gray-500">
                      {new Date(c.created_at).toLocaleDateString("zh-CN")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {ivBadge && (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ivBadge.cls}`}>
                        {ivBadge.label}
                      </span>
                    )}
                    {latest?.has_summary && (
                      <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-100 text-indigo-700">
                        有总结
                      </span>
                    )}
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        c.has_match
                          ? "bg-green-100 text-green-700"
                          : "bg-amber-100 text-amber-700 animate-pulse"
                      }`}
                    >
                      {c.has_match ? "已评分" : "评分中..."}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
