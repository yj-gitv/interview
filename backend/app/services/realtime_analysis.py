from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.config import settings


@dataclass
class AnalysisResult:
    current_question_index: int = -1
    elements_checked: list[str] = field(default_factory=list)
    follow_up_suggestions: list[str] = field(default_factory=list)
    instant_rating: str = ""
    instant_comment: str = ""


REALTIME_SYSTEM_PROMPT = """你是一位面试辅助AI。根据当前面试转录和问题清单，实时分析并提供辅助。

重要：所有输出内容（追问建议、评语等）必须使用中文。

任务：
1. 判断当前正在讨论的问题（通过语义匹配，而非逐字对照）
2. 检查候选人回答中已覆盖的优秀要素
3. 生成追问建议（当回答缺乏具体案例/数据、与简历有出入、过于简短、或出现有价值新话题时）
4. 给出即时评价（好/一般/差）

返回JSON格式：
{
  "current_question_index": number,
  "elements_checked": ["已覆盖的要素"],
  "follow_up_suggestions": ["追问建议1", "追问建议2"],
  "instant_rating": "好/一般/差/空字符串",
  "instant_comment": "一句话评语"
}"""


class RealtimeAnalysisService:
    def __init__(self, llm_client: LLMClient | None = None):
        self._llm = llm_client

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._llm

    async def _call_llm(self, prompt: str) -> dict:
        llm = self._get_llm()
        return await llm.chat_json(
            prompt=prompt,
            model=settings.openai_model_fast,
            system=REALTIME_SYSTEM_PROMPT,
        )

    async def analyze(
        self,
        transcript_so_far: str,
        questions: list[dict],
        current_question_index: int = 0,
    ) -> AnalysisResult:
        questions_text = "\n".join(
            f"[{i}] {q.get('question', '')} (考察: {q.get('purpose', '')}; "
            f"优秀要素: {', '.join(q.get('good_answer_elements', []))})"
            for i, q in enumerate(questions)
        )

        prompt = (
            f"## 面试问题清单\n{questions_text}\n\n"
            f"## 当前问题索引: {current_question_index}\n\n"
            f"## 面试转录（最近内容）\n{transcript_so_far[-2000:]}"
        )

        data = await self._call_llm(prompt)
        return AnalysisResult(
            current_question_index=data.get("current_question_index", current_question_index),
            elements_checked=data.get("elements_checked", []),
            follow_up_suggestions=data.get("follow_up_suggestions", []),
            instant_rating=data.get("instant_rating", ""),
            instant_comment=data.get("instant_comment", ""),
        )
