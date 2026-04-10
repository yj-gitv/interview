import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Position } from "../api/client";

export default function PositionList() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [jdText, setJdText] = useState("");

  useEffect(() => {
    api.positions.list().then(setPositions);
  }, []);

  const handleCreate = async () => {
    if (!title.trim() || !jdText.trim()) return;
    await api.positions.create({ title, department, jd_text: jdText });
    setTitle("");
    setDepartment("");
    setJdText("");
    setShowForm(false);
    const updated = await api.positions.list();
    setPositions(updated);
  };

  const statusLabel: Record<string, string> = {
    open: "招聘中",
    closed: "已关闭",
    paused: "暂停",
  };

  const statusColor: Record<string, string> = {
    open: "bg-green-100 text-green-700",
    closed: "bg-gray-100 text-gray-600",
    paused: "bg-yellow-100 text-yellow-700",
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">岗位管理</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? "取消" : "新建岗位"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              岗位名称
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="如：产品经理"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              部门
            </label>
            <input
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="如：产品部"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              岗位描述（JD）
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="粘贴完整的岗位描述..."
            />
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
          >
            创建
          </button>
        </div>
      )}

      {positions.length === 0 && !showForm ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg mb-2">暂无岗位</p>
          <p className="text-sm">点击「新建岗位」开始添加</p>
        </div>
      ) : (
        <div className="space-y-3">
          {positions.map((p) => (
            <Link
              key={p.id}
              to={`/positions/${p.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{p.title}</h3>
                  {p.department && (
                    <span className="text-sm text-gray-500">
                      {p.department}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500">
                    {p.candidate_count} 位候选人
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor[p.status] || ""}`}
                  >
                    {statusLabel[p.status] || p.status}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
