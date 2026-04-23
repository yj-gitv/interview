import { useState } from "react";
import type { EvaluationCriterion } from "../api/client";

const WEIGHT_LABELS: Record<EvaluationCriterion["weight"], string> = {
  high: "\u9ad8",
  medium: "\u4e2d",
  low: "\u4f4e",
};

const WEIGHT_COLORS: Record<EvaluationCriterion["weight"], string> = {
  high: "bg-red-100 text-red-700 border-red-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-gray-100 text-gray-600 border-gray-200",
};

interface CriteriaEditorProps {
  criteria: EvaluationCriterion[];
  onChange: (criteria: EvaluationCriterion[]) => void;
  readonly?: boolean;
}

export default function CriteriaEditor({
  criteria,
  onChange,
  readonly = false,
}: CriteriaEditorProps) {
  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [draft, setDraft] = useState<EvaluationCriterion>({
    name: "",
    description: "",
    weight: "medium",
  });

  const startAdd = () => {
    setDraft({ name: "", description: "", weight: "medium" });
    setEditingIdx(-1);
  };

  const startEdit = (idx: number) => {
    setDraft({ ...criteria[idx] });
    setEditingIdx(idx);
  };

  const cancel = () => setEditingIdx(null);

  const save = () => {
    if (!draft.name.trim()) return;
    const trimmed = {
      ...draft,
      name: draft.name.trim(),
      description: draft.description.trim(),
    };
    if (editingIdx === -1) {
      onChange([...criteria, trimmed]);
    } else if (editingIdx !== null) {
      const next = [...criteria];
      next[editingIdx] = trimmed;
      onChange(next);
    }
    setEditingIdx(null);
  };

  const remove = (idx: number) => {
    onChange(criteria.filter((_, i) => i !== idx));
    if (editingIdx === idx) setEditingIdx(null);
  };

  const move = (idx: number, dir: -1 | 1) => {
    const target = idx + dir;
    if (target < 0 || target >= criteria.length) return;
    const next = [...criteria];
    [next[idx], next[target]] = [next[target], next[idx]];
    onChange(next);
  };

  return (
    <div>
      {criteria.length === 0 && editingIdx === null && (
        <p className="text-sm text-gray-400 mb-3">
          {"\u6682\u672a\u8bbe\u7f6e\u8003\u5bdf\u7ef4\u5ea6\u3002\u6dfb\u52a0\u540e\u5c06\u5f71\u54cd\u7b80\u5386\u8bc4\u5206\u3001\u9762\u8bd5\u95ee\u9898\u751f\u6210\u3001\u8ffd\u95ee\u5efa\u8bae\u548c\u9762\u8bd5\u603b\u7ed3\u3002"}
        </p>
      )}

      <div className="space-y-2">
        {criteria.map((c, i) => (
          <div
            key={i}
            className="flex items-start gap-3 bg-white border border-gray-200 rounded-lg px-3 py-2.5 hover:border-blue-300 transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900 text-sm">
                  {c.name}
                </span>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded border font-medium ${WEIGHT_COLORS[c.weight]}`}
                >
                  {WEIGHT_LABELS[c.weight]}
                  {"\u4f18\u5148"}
                </span>
              </div>
              {c.description && (
                <p className="text-xs text-gray-500 mt-0.5 whitespace-pre-wrap">
                  {c.description}
                </p>
              )}
            </div>
            {!readonly && (
              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  onClick={() => move(i, -1)}
                  disabled={i === 0}
                  className="px-1.5 py-0.5 text-xs text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                  title={"\u4e0a\u79fb"}
                >
                  {"\u2191"}
                </button>
                <button
                  type="button"
                  onClick={() => move(i, 1)}
                  disabled={i === criteria.length - 1}
                  className="px-1.5 py-0.5 text-xs text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                  title={"\u4e0b\u79fb"}
                >
                  {"\u2193"}
                </button>
                <button
                  type="button"
                  onClick={() => startEdit(i)}
                  className="px-2 py-0.5 text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  {"\u7f16\u8f91"}
                </button>
                <button
                  type="button"
                  onClick={() => remove(i)}
                  className="px-2 py-0.5 text-xs text-red-500 hover:text-red-700 font-medium"
                >
                  {"\u5220\u9664"}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {editingIdx !== null && (
        <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50/50 space-y-2.5">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {"\u7ef4\u5ea6\u540d\u79f0 *"}
            </label>
            <input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              className="w-full px-2.5 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder={
                "\u5982\uff1a\u6570\u636e\u9a71\u52a8\u51b3\u7b56\u3001\u8de8\u90e8\u95e8\u534f\u4f5c\u3001\u7528\u6237\u6d1e\u5bdf\u529b"
              }
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {"\u8be6\u7ec6\u8bf4\u660e"}
            </label>
            <textarea
              value={draft.description}
              onChange={(e) =>
                setDraft({ ...draft, description: e.target.value })
              }
              rows={2}
              className="w-full px-2.5 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
              placeholder={
                "\u5bf9\u8be5\u7ef4\u5ea6\u7684\u5177\u4f53\u671f\u671b\uff0c\u5e2e\u52a9 AI \u66f4\u7cbe\u51c6\u5730\u51fa\u9898\u548c\u8bc4\u4f30"
              }
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {"\u4f18\u5148\u7ea7"}
            </label>
            <div className="flex gap-2">
              {(["high", "medium", "low"] as const).map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => setDraft({ ...draft, weight: w })}
                  className={`px-3 py-1 rounded-md text-sm font-medium border transition-colors ${
                    draft.weight === w
                      ? WEIGHT_COLORS[w] + " ring-2 ring-offset-1 ring-blue-400"
                      : "bg-white text-gray-500 border-gray-200 hover:bg-gray-50"
                  }`}
                >
                  {WEIGHT_LABELS[w]}
                </button>
              ))}
            </div>
          </div>
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={save}
              disabled={!draft.name.trim()}
              className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {editingIdx === -1 ? "\u6dfb\u52a0" : "\u4fdd\u5b58"}
            </button>
            <button
              type="button"
              onClick={cancel}
              className="px-3 py-1.5 bg-white text-gray-600 text-sm font-medium rounded-md border border-gray-300 hover:bg-gray-50"
            >
              {"\u53d6\u6d88"}
            </button>
          </div>
        </div>
      )}

      {!readonly && editingIdx === null && (
        <button
          type="button"
          onClick={startAdd}
          className="mt-3 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
        >
          {"+ \u6dfb\u52a0\u8003\u5bdf\u7ef4\u5ea6"}
        </button>
      )}
    </div>
  );
}
