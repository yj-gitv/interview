from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.config import settings


@dataclass
class Question:
    question: str
    purpose: str
    good_answer_elements: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


@dataclass
class QuestionSet:
    opening: list[Question] = field(default_factory=list)
    experience_verification: list[Question] = field(default_factory=list)
    competency: list[Question] = field(default_factory=list)
    risk_probing: list[Question] = field(default_factory=list)
    culture_fit: list[Question] = field(default_factory=list)


QUESTION_SYSTEM_PROMPT = """你是一位资深面试官，擅长为非技术岗位（产品、运营、市场、设计等）设计结构化面试问题。

请根据JD、候选人简历、匹配分析结果，生成结构化面试问题清单。每个问题需要包含：
- question: 问题本身
- purpose: 考察目的
- good_answer_elements: 优秀回答应包含的要素（数组）
- red_flags: 红旗信号（数组）

返回JSON格式：
{
  "opening": [1-2个开场问题],
  "experience_verification": [3-5个经历验证问题，用STAR法],
  "competency": [3-5个能力考察问题，情景题为主],
  "risk_probing": [1-3个风险探测问题],
  "culture_fit": [1-2个文化匹配问题]
}"""


def _parse_questions(items: list[dict]) -> list[Question]:
    return [
        Question(
            question=item.get("question", ""),
            purpose=item.get("purpose", ""),
            good_answer_elements=item.get("good_answer_elements", []),
            red_flags=item.get("red_flags", []),
        )
        for item in items
    ]


class QuestionGenService:
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
            system=QUESTION_SYSTEM_PROMPT,
        )

    async def generate(
        self,
        jd_text: str,
        resume_text: str,
        match_highlights: list[str],
        match_risks: list[str],
        preferences: str = "",
    ) -> QuestionSet:
        prompt = (
            f"## 岗位JD\n{jd_text}\n\n"
            f"## 候选人简历（已脱敏）\n{resume_text}\n\n"
            f"## 匹配分析亮点\n" + "\n".join(f"- {h}" for h in match_highlights) + "\n\n"
            f"## 匹配分析风险\n" + "\n".join(f"- {r}" for r in match_risks)
        )
        if preferences:
            prompt += f"\n\n## 面试官关注点\n{preferences}"

        data = await self._call_llm(prompt)
        return QuestionSet(
            opening=_parse_questions(data.get("opening", [])),
            experience_verification=_parse_questions(data.get("experience_verification", [])),
            competency=_parse_questions(data.get("competency", [])),
            risk_probing=_parse_questions(data.get("risk_probing", [])),
            culture_fit=_parse_questions(data.get("culture_fit", [])),
        )
