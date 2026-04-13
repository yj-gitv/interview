import { useEffect, useState } from "react";
import { api } from "../api/client";

interface AppSettings {
  auto_cleanup_enabled: boolean;
  auto_cleanup_days: number;
  whisper_model: string;
  audio_device_name: string;
}

export default function Settings() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [cleanupDays, setCleanupDays] = useState(90);
  const [cleaning, setCleaning] = useState(false);
  const [cleanResult, setCleanResult] = useState<{
    interviews: number;
    transcripts: number;
    candidates: number;
    summaries: number;
  } | null>(null);

  useEffect(() => {
    api.settings.get().then((s) => {
      setSettings(s);
      setCleanupDays(s.auto_cleanup_days);
    });
  }, []);

  const handleCleanup = async () => {
    setCleaning(true);
    setCleanResult(null);
    try {
      const result = await api.settings.cleanup(cleanupDays);
      setCleanResult(result);
    } finally {
      setCleaning(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-bold text-gray-900 mb-6">系统设置</h2>

      {/* Current Config */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <h3 className="font-semibold text-gray-900 mb-4">当前配置</h3>
        {settings ? (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">语音识别模型</span>
              <p className="font-medium text-gray-900 mt-0.5">{settings.whisper_model}</p>
            </div>
            <div>
              <span className="text-gray-500">音频输入设备</span>
              <p className="font-medium text-gray-900 mt-0.5">{settings.audio_device_name || "未配置"}</p>
            </div>
            <div>
              <span className="text-gray-500">自动清理</span>
              <p className="font-medium text-gray-900 mt-0.5">
                {settings.auto_cleanup_enabled ? `已启用（${settings.auto_cleanup_days} 天）` : "未启用"}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">加载中...</p>
        )}
        <p className="text-xs text-gray-400 mt-4 pt-3 border-t border-gray-100">
          配置通过环境变量或 .env 文件修改，前缀为 INTERVIEW_
        </p>
      </div>

      {/* Manual Cleanup */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="font-semibold text-gray-900 mb-2">手动数据清理</h3>
        <p className="text-sm text-gray-500 mb-4">
          删除指定天数之前的已完成面试及相关数据（转录、评估、总结、导出文件）。
          超过保留期且无近期面试的候选人也会被清理。
        </p>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-700">保留天数</label>
          <input
            type="number"
            min={1}
            max={3650}
            value={cleanupDays}
            onChange={(e) => setCleanupDays(Number(e.target.value))}
            className="w-24 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            onClick={handleCleanup}
            disabled={cleaning}
            className="px-4 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 transition-colors"
          >
            {cleaning ? "清理中..." : "执行清理"}
          </button>
        </div>

        {cleanResult && (
          <div className="mt-4 bg-gray-50 rounded-lg p-3 text-sm">
            <p className="font-medium text-gray-800 mb-1">清理完成</p>
            <div className="grid grid-cols-2 gap-1 text-gray-600">
              <span>面试：{cleanResult.interviews} 条</span>
              <span>转录：{cleanResult.transcripts} 条</span>
              <span>总结：{cleanResult.summaries} 条</span>
              <span>候选人：{cleanResult.candidates} 人</span>
            </div>
          </div>
        )}
      </div>

      {/* Environment Variables Reference */}
      <div className="mt-6 bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="font-semibold text-gray-900 mb-3">环境变量参考</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left">
                <th className="pb-2 font-medium text-gray-700">变量名</th>
                <th className="pb-2 font-medium text-gray-700">说明</th>
              </tr>
            </thead>
            <tbody className="text-gray-600">
              {[
                ["INTERVIEW_OPENAI_API_KEY", "LLM API 密钥"],
                ["INTERVIEW_OPENAI_BASE_URL", "LLM API 地址"],
                ["INTERVIEW_WHISPER_MODEL", "Whisper 模型 (tiny/base/small/medium)"],
                ["INTERVIEW_AUDIO_DEVICE_NAME", "音频输入设备名称"],
                ["INTERVIEW_DINGTALK_WEBHOOK_URL", "钉钉机器人 Webhook"],
                ["INTERVIEW_FEISHU_WEBHOOK_URL", "飞书机器人 Webhook"],
                ["INTERVIEW_AUTO_CLEANUP_ENABLED", "自动清理开关 (true/false)"],
                ["INTERVIEW_AUTO_CLEANUP_DAYS", "数据保留天数"],
              ].map(([k, v]) => (
                <tr key={k} className="border-b border-gray-50">
                  <td className="py-1.5 font-mono text-xs text-gray-800">{k}</td>
                  <td className="py-1.5">{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
