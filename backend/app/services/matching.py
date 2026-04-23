from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.services.criteria_utils import format_criteria_section
from app.config import settings


@dataclass
class MatchResult:
    experience_score: float
    experience_note: str
    industry_score: float
    industry_note: str
    competency_score: float
    competency_note: str
    potential_score: float
    potential_note: str
    overall_score: float
    recommendation: str
    highlights: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


MATCH_SYSTEM_PROMPT = """你是一位资深HR，擅长分析简历与岗位匹配度。请根据提供的JD和简历进行多维度评估。

重要：无论简历使用何种语言，所有分析说明、亮点、风险和推荐评语都必须使用中文输出。

评分标准（每项0-100分）：
- experience_score: 岗位经验匹配度
- industry_score: 行业背景相关性
- competency_score: 核心能力匹配度（如果面试官提供了自定义考察维度，请重点基于这些维度评估）
- potential_score: 成长潜力评估
- overall_score: 综合推荐指数（如有自定义考察维度，高优先维度的得分应占更大权重）

recommendation 取值：推荐 / 待定 / 不推荐

返回JSON格式：
{
  "experience_score": number,
  "experience_note": "简短说明",
  "industry_score": number,
  "industry_note": "简短说明",
  "competency_score": number,
  "competency_note": "简短说明",
  "potential_score": number,
  "potential_note": "简短说明",
  "overall_score": number,
  "recommendation": "推荐/待定/不推荐",
  "highlights": ["亮点1", "亮点2"],
  "risks": ["风险1"]
}"""


class MatchingService:
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
            model=settings.openai_model_strong,
            system=MATCH_SYSTEM_PROMPT,
        )

    async def match(
        self,
        jd_text: str,
        resume_text: str,
        preferences: str = "",
    ) -> MatchResult:
        prompt = f"## 岗位JD\n{jd_text}\n\n## 候选人简历（已脱敏）\n{resume_text}"
        prompt += format_criteria_section(
            preferences,
            "面试官自定义考察重点",
            "请基于以上考察维度调整评分权重，在亮点和风险中重点体现与这些维度的匹配/差距。",
        )

        data = await self._call_llm(prompt)
        return MatchResult(
            experience_score=data.get("experience_score", 0),
            experience_note=data.get("experience_note", ""),
            industry_score=data.get("industry_score", 0),
            industry_note=data.get("industry_note", ""),
            competency_score=data.get("competency_score", 0),
            competency_note=data.get("competency_note", ""),
            potential_score=data.get("potential_score", 0),
            potential_note=data.get("potential_note", ""),
            overall_score=data.get("overall_score", 0),
            recommendation=data.get("recommendation", "待定"),
            highlights=data.get("highlights", []),
            risks=data.get("risks", []),
        )
