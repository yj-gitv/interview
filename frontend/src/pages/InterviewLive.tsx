import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, Interview, WsMessage, QuestionItem } from "../api/client";

interface TranscriptLine {
  speaker: string;
  text: string;
  timestamp: number;
}

interface Suggestion {
  text: string;
  timestamp: number;
  isNew: boolean;
}

const TARGET_SAMPLE_RATE = 16000;
const CHUNK_SECONDS = 6;
const CHUNK_SIZE = TARGET_SAMPLE_RATE * CHUNK_SECONDS;

function downsample(buffer: Float32Array, fromRate: number, toRate: number): Float32Array {
  if (fromRate === toRate) return buffer;
  const ratio = fromRate / toRate;
  const newLength = Math.round(buffer.length / ratio);
  const result = new Float32Array(newLength);
  for (let i = 0; i < newLength; i++) {
    const srcIndex = i * ratio;
    const lo = Math.floor(srcIndex);
    const hi = Math.min(lo + 1, buffer.length - 1);
    const frac = srcIndex - lo;
    result[i] = buffer[lo] * (1 - frac) + buffer[hi] * frac;
  }
  return result;
}

export default function InterviewLive() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [interview, setInterview] = useState<Interview | null>(null);
  const [questions, setQuestions] = useState<
    (QuestionItem & { index: number })[]
  >([]);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [transcripts, setTranscripts] = useState<TranscriptLine[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [elementsChecked, setElementsChecked] = useState<string[]>([]);
  const [instantRating, setInstantRating] = useState("");
  const [instantComment, setInstantComment] = useState("");
  const [connected, setConnected] = useState(false);
  const [audioActive, setAudioActive] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [manualText, setManualText] = useState("");
  const [manualSpeaker, setManualSpeaker] = useState<
    "interviewer" | "candidate"
  >("candidate");
  const [elapsed, setElapsed] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<number>();
  const audioCtxRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  useEffect(() => {
    if (!id) return;
    api.interviews.get(Number(id)).then((iv) => {
      setInterview(iv);
      if (iv.questions_json) {
        try {
          const qs = JSON.parse(iv.questions_json);
          const allQs: (QuestionItem & { index: number })[] = [];
          const sections = [
            "opening",
            "experience_verification",
            "competency",
            "risk_probing",
            "culture_fit",
          ];
          if (Array.isArray(qs)) {
            qs.forEach((q: QuestionItem, i: number) =>
              allQs.push({ ...q, index: i })
            );
          } else {
            let idx = 0;
            for (const section of sections) {
              if (qs[section]) {
                for (const q of qs[section]) {
                  allQs.push({ ...q, index: idx++ });
                }
              }
            }
          }
          setQuestions(allQs);
        } catch {
          /* ignore parse errors */
        }
      }
    });
  }, [id]);

  const connectWs = useCallback(() => {
    if (!id) return;
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${window.location.host}/ws/interview/${id}`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data);
      if (msg.type === "error") {
        setAudioError((msg as { type: "error"; message: string }).message);
        return;
      }
      if (msg.type === "transcript") {
        setTranscripts((prev) => [
          ...prev,
          {
            speaker: msg.speaker,
            text: msg.text,
            timestamp: msg.timestamp,
          },
        ]);
      } else if (msg.type === "analysis") {
        setCurrentQIndex(msg.current_question_index);
        setElementsChecked(msg.elements_checked);
        if (msg.follow_up_suggestions.length > 0) {
          const now = Date.now();
          setSuggestions((prev) => {
            const updated = prev.map((s) => ({ ...s, isNew: false }));
            const newOnes = msg.follow_up_suggestions.map((text) => ({
              text,
              timestamp: now,
              isNew: true,
            }));
            return [...newOnes, ...updated];
          });
        }
        if (msg.instant_rating) setInstantRating(msg.instant_rating);
        if (msg.instant_comment) setInstantComment(msg.instant_comment);
      } else if (msg.type === "question_switched") {
        setCurrentQIndex(msg.current_question_index);
      }
    };
    wsRef.current = ws;
  }, [id]);

  useEffect(() => {
    if (!id || !interview) return;
    if (interview.status === "in_progress" && !connected && !wsRef.current) {
      api.interviews.createSession(Number(id)).catch(() => {}).then(() => {
        connectWs();
        if (!timerRef.current) {
          timerRef.current = window.setInterval(() => setElapsed((e) => e + 1), 1000);
        }
      });
    }
  }, [id, interview, connected, connectWs]);

  useEffect(() => {
    async function loadDevices() {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter((d) => d.kind === "audioinput");
        setAudioDevices(audioInputs);
        const voicemeeter = audioInputs.find((d) =>
          d.label.toLowerCase().includes("voicemeeter")
        );
        if (voicemeeter) setSelectedDeviceId(voicemeeter.deviceId);
      } catch {
        /* permission denied — devices will be empty */
      }
    }
    loadDevices();
  }, []);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  const handleStartInterview = async () => {
    if (!id) return;
    setStarting(true);
    setAudioError(null);
    try {
      await api.interviews.createSession(Number(id));
      await api.interviews.start(Number(id));
      setInterview((prev) =>
        prev ? { ...prev, status: "in_progress" } : prev
      );
      connectWs();
      timerRef.current = window.setInterval(() => setElapsed((e) => e + 1), 1000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setAudioError(`开始面试失败：${msg}`);
    } finally {
      setStarting(false);
    }
  };

  const stopBrowserAudio = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
  }, []);

  const handleStartAudio = useCallback(async () => {
    setAudioError(null);
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setAudioError("WebSocket 未连接，请先开始面试");
      return;
    }

    try {
      const micConstraints: MediaStreamConstraints = {
        audio: selectedDeviceId
          ? { deviceId: { exact: selectedDeviceId } }
          : true,
      };
      const micStream = await navigator.mediaDevices.getUserMedia(micConstraints);

      let systemStream: MediaStream | null = null;
      try {
        systemStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true,
        } as DisplayMediaStreamOptions);
        systemStream.getVideoTracks().forEach((t) => t.stop());
      } catch {
        // User declined screen share — mic-only mode is fine
      }

      const audioCtx = new AudioContext();
      audioCtxRef.current = audioCtx;
      const nativeSR = audioCtx.sampleRate;

      const allTracks = [...micStream.getTracks()];
      if (systemStream) allTracks.push(...systemStream.getTracks());
      mediaStreamRef.current = new MediaStream(allTracks);

      // 0x01 = mic (interviewer), 0x02 = system (candidate)
      function createTaggedSender(stream: MediaStream, tag: number) {
        const src = audioCtx.createMediaStreamSource(stream);
        const proc = audioCtx.createScriptProcessor(4096, 1, 1);
        let buf: Float32Array[] = [];
        let len = 0;

        proc.onaudioprocess = (e) => {
          const raw = e.inputBuffer.getChannelData(0);
          const resampled = downsample(raw, nativeSR, TARGET_SAMPLE_RATE);
          buf.push(new Float32Array(resampled));
          len += resampled.length;

          if (len >= CHUNK_SIZE) {
            const pcm = new Float32Array(len);
            let off = 0;
            for (const b of buf) { pcm.set(b, off); off += b.length; }
            buf = [];
            len = 0;

            if (ws && ws.readyState === WebSocket.OPEN) {
              const tagged = new Uint8Array(1 + pcm.byteLength);
              tagged[0] = tag;
              tagged.set(new Uint8Array(pcm.buffer), 1);
              ws.send(tagged.buffer);
            }
          }
        };
        src.connect(proc);
        proc.connect(audioCtx.destination);
        return proc;
      }

      const micProc = createTaggedSender(micStream, 0x01);
      processorRef.current = micProc;

      if (systemStream && systemStream.getAudioTracks().length > 0) {
        createTaggedSender(systemStream, 0x02);
      }

      ws.send(JSON.stringify({ type: "start_browser_audio" }));
      setAudioActive(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setAudioError(`音频访问失败：${msg}`);
    }
  }, [selectedDeviceId]);

  const handleEndInterview = async () => {
    if (!id) return;
    if (timerRef.current) clearInterval(timerRef.current);
    stopBrowserAudio();
    await api.interviews.end(Number(id));
    await api.interviews.stopSession(Number(id));
    wsRef.current?.close();
    navigate(`/interviews/${id}/summary`);
  };

  const handleManualInput = () => {
    if (!manualText.trim() || !wsRef.current) return;
    wsRef.current.send(
      JSON.stringify({
        type: "manual_input",
        speaker: manualSpeaker,
        text: manualText,
      })
    );
    setManualText("");
  };

  const handleSwitchQuestion = (index: number) => {
    setCurrentQIndex(index);
    wsRef.current?.send(JSON.stringify({ type: "switch_question", index }));
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  if (!interview) return <div className="text-gray-500">Loading...</div>;

  const ratingColor: Record<string, string> = {
    好: "text-green-600",
    一般: "text-yellow-600",
    差: "text-red-600",
  };

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      {/* Top Bar */}
      <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <Link
            to={`/candidates/${interview.candidate_id}`}
            className="text-gray-400 hover:text-gray-700 transition-colors"
            title="返回候选人"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
          </Link>
          <span className="font-semibold text-gray-900">
            {interview.candidate_codename}
          </span>
          <span className="text-sm text-gray-500">
            {interview.position_title}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              connected
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            {connected ? "已连接" : "未连接"}
          </span>
          {audioActive && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 animate-pulse">
              录音中
            </span>
          )}
          {audioError && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-800">
              {audioError}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-lg text-gray-700">
            {formatTime(elapsed)}
          </span>
          {interview.status !== "in_progress" ? (
            <button
              onClick={handleStartInterview}
              disabled={starting}
              className="px-4 py-1.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {starting ? "准备中…" : "开始面试"}
            </button>
          ) : (
            <>
              {!audioActive && (
                <>
                  {audioDevices.length > 1 && (
                    <select
                      value={selectedDeviceId}
                      onChange={(e) => setSelectedDeviceId(e.target.value)}
                      className="text-xs border border-gray-300 rounded px-1 py-1 max-w-[180px] truncate"
                    >
                      {audioDevices.map((d) => (
                        <option key={d.deviceId} value={d.deviceId}>
                          {d.label || `麦克风 ${d.deviceId.slice(0, 8)}`}
                        </option>
                      ))}
                    </select>
                  )}
                  <button
                    onClick={handleStartAudio}
                    className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                  >
                    启动音频
                  </button>
                </>
              )}
              <button
                onClick={handleEndInterview}
                className="px-4 py-1.5 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700"
              >
                结束面试
              </button>
            </>
          )}
        </div>
      </div>

      {/* Three-Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Transcription */}
        <div className="w-1/3 border-r border-gray-200 flex flex-col bg-white">
          <div className="px-3 py-2 border-b border-gray-100 text-sm font-semibold text-gray-700">
            实时转录
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {transcripts.map((t, i) => (
              <div
                key={i}
                className={`text-sm ${
                  t.speaker === "interviewer"
                    ? "text-blue-700"
                    : "text-orange-700"
                }`}
              >
                <span className="text-xs text-gray-400 mr-2">
                  {formatTime(Math.round(t.timestamp))}
                </span>
                <span className="font-medium">
                  {t.speaker === "interviewer" ? "面试官" : "候选人"}:
                </span>{" "}
                {t.text}
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>
          {connected && (
            <div className="border-t border-gray-200 p-2 flex gap-2">
              <select
                value={manualSpeaker}
                onChange={(e) =>
                  setManualSpeaker(e.target.value as "interviewer" | "candidate")
                }
                className="text-xs border border-gray-300 rounded px-1"
              >
                <option value="interviewer">面试官</option>
                <option value="candidate">候选人</option>
              </select>
              <input
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleManualInput()}
                placeholder="手动输入..."
                className="flex-1 text-sm border border-gray-300 rounded px-2 py-1"
              />
              <button
                onClick={handleManualInput}
                className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
              >
                发送
              </button>
            </div>
          )}
        </div>

        {/* Center: Question Checklist */}
        <div className="w-1/3 border-r border-gray-200 flex flex-col bg-white">
          <div className="px-3 py-2 border-b border-gray-100 text-sm font-semibold text-gray-700">
            问题清单 & 要素检查
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {questions.map((q, i) => {
              const isCurrent = i === currentQIndex;
              const isPast = i < currentQIndex;
              return (
                <div
                  key={i}
                  onClick={() => handleSwitchQuestion(i)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isCurrent
                      ? "border-blue-400 bg-blue-50 shadow-sm"
                      : isPast
                        ? "border-gray-200 bg-gray-50 opacity-60"
                        : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <p
                    className={`text-sm font-medium ${
                      isCurrent ? "text-blue-900" : "text-gray-700"
                    }`}
                  >
                    {q.question}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{q.purpose}</p>
                  {isCurrent && q.good_answer_elements && (
                    <div className="mt-2 space-y-1">
                      {q.good_answer_elements.map((el, j) => {
                        const checked = elementsChecked.includes(el);
                        return (
                          <div key={j} className="flex items-center gap-1.5">
                            <span
                              className={`text-xs ${
                                checked ? "text-green-600" : "text-gray-400"
                              }`}
                            >
                              {checked ? "✓" : "○"}
                            </span>
                            <span
                              className={`text-xs ${
                                checked
                                  ? "text-green-700"
                                  : "text-gray-500"
                              }`}
                            >
                              {el}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {isCurrent && instantRating && (
                    <div className="mt-2 flex items-center gap-2">
                      <span
                        className={`text-xs font-semibold ${
                          ratingColor[instantRating] || "text-gray-600"
                        }`}
                      >
                        {instantRating}
                      </span>
                      {instantComment && (
                        <span className="text-xs text-gray-500">
                          {instantComment}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Suggestions */}
        <div className="w-1/3 flex flex-col bg-white">
          <div className="px-3 py-2 border-b border-gray-100 text-sm font-semibold text-gray-700">
            追问建议
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {suggestions.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                面试开始后，AI 将在此处提供追问建议
              </div>
            ) : (
              suggestions.map((s, i) => (
                <div
                  key={`${s.timestamp}-${i}`}
                  className={`p-3 rounded-lg border transition-all ${
                    s.isNew
                      ? "border-blue-300 bg-blue-50 shadow-sm"
                      : "border-gray-200 bg-gray-50 text-sm opacity-80"
                  }`}
                >
                  <p
                    className={
                      s.isNew
                        ? "text-sm text-blue-900 font-medium"
                        : "text-xs text-gray-600"
                    }
                  >
                    {s.text}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
