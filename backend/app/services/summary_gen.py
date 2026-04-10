import json
from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.config import settings


@dataclass
class SummaryResult:
    candidate_overview: str = ""
    expression_score: float = 0
    case_richness_score: float = 0
    depth_score: float = 0
    self_awareness_score: float = 0
    enthusiasm_score: float = 0
    overall_score: float = 0
    highlights: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    jd_alignment: list[dict] = field(default_factory=list)
    recommendation: str = "待定"
    recommendation_reason: str = ""
    next_steps: str = ""


SUMMARY_SYSTEM_PROMPT = """你是一位资深HR，需要根据完整面试转录生成结构化面试总结报告。

评估维度（每项0-100分）：
- expression_score: 表达清晰度（逻辑是否清楚、言之有物）
- case_richness_score: 案例丰富度（是否用具体案例支撑观点）
- depth_score: 思维深度（分析问题的层次和全面性）
- self_awareness_score: 自我认知（对自身优劣势的真实认知）
- enthusiasm_score: 岗位热情（对岗位和公司的了解和兴趣）
- overall_score: 综合评分

recommendation 取值：推荐 / 待定 / 不推荐

返回JSON格式：
{
  "candidate_overview": "一段话总结候选人",
  "expression_score": number,
  "case_richness_score": number,
  "depth_score": number,
  "self_awareness_score": number,
  "enthusiasm_score": number,
  "overall_score": number,
  "highlights": ["亮点1", "亮点2", "亮点3"],
  "concerns": ["顾虑点1", "顾虑点2"],
  "jd_alignment": [
    {"requirement": "JD要求项", "status": "达成/部分达成/未达成", "note": "说明"}
  ],
  "recommendation": "推荐/待定/不推荐",
  "recommendation_reason": "推荐理由",
  "next_steps": "后续建议（下一轮重点考察方向）"
}"""


class SummaryGenService:
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
            system=SUMMARY_SYSTEM_PROMPT,
        )

    async def generate(
        self,
        transcript: str,
        jd_text: str,
        resume_text: str = "",
        match_data: dict | None = None,
    ) -> SummaryResult:
        prompt = f"## 岗位JD\n{jd_text}\n\n## 完整面试转录\n{transcript}"
        if resume_text:
            prompt += f"\n\n## 候选人简历（脱敏）\n{resume_text}"
        if match_data:
            prompt += f"\n\n## 简历匹配评分\n{json.dumps(match_data, ensure_ascii=False)}"

        data = await self._call_llm(prompt)
        return SummaryResult(
            candidate_overview=data.get("candidate_overview", ""),
            expression_score=data.get("expression_score", 0),
            case_richness_score=data.get("case_richness_score", 0),
            depth_score=data.get("depth_score", 0),
            self_awareness_score=data.get("self_awareness_score", 0),
            enthusiasm_score=data.get("enthusiasm_score", 0),
            overall_score=data.get("overall_score", 0),
            highlights=data.get("highlights", []),
            concerns=data.get("concerns", []),
            jd_alignment=data.get("jd_alignment", []),
            recommendation=data.get("recommendation", "待定"),
            recommendation_reason=data.get("recommendation_reason", ""),
            next_steps=data.get("next_steps", ""),
        )
