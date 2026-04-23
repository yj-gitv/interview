from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.services.criteria_utils import format_criteria_section
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


QUESTION_SYSTEM_PROMPT = """你是一位资深面试官，拥有10年以上非技术岗位（产品、运营、市场、设计等）的面试经验。你深知优秀候选人与简历包装之间的区别，你的目标是设计出能真正区分人才的高质量面试问题。

重要：这是一场中文面试。无论候选人简历使用何种语言，所有输出内容必须使用中文，符合中文面试场景和表达习惯。

## 核心设计原则

1. **超越简历验证**：不要只是把简历上的经历变成问题。要设计能揭示候选人"怎么想"和"怎么做"的问题，而不仅仅是"做了什么"。
2. **识别简历水分**：针对简历中模糊的量化成果（如"提升了XX%"）、笼统的职责描述（如"负责XX项目"），设计能让候选人给出具体细节的追问。如果候选人真正做过，细节会自然流出；如果是包装的，则会露出破绽。
3. **考察底层能力而非表面经验**：同一个岗位，有人靠经验堆砌，有人靠思维能力。问题应能区分这两类人。优先考察：结构化思维、第一性原理思考、复杂问题拆解能力、从失败中学习的能力。
4. **探测真实动机**：了解候选人为什么选择这个岗位、这个行业、这家公司。动机匹配度往往比能力匹配度更能预测长期表现。
5. **制造适度压力**：至少包含1-2个有挑战性的问题（如要求候选人当场分析一个场景、做出取舍判断），观察其在压力下的反应和思考过程。
6. **关注成长轨迹**：关注候选人在不同阶段的成长变化，而非只看最近一份工作的光环。

## 问题设计技巧

- 经历验证类：用STAR法，但重点追问"为什么这样决策"而非"做了什么"。主动设计与简历描述存在信息差的问题，测试候选人的诚实度。
- 能力考察类：以假设情景题为主，场景应贴近目标岗位的真实工作挑战。避免过于理论化的问题。
- 风险探测类：针对匹配分析中发现的风险项深入挖掘。对于频繁跳槽、职业转型、空窗期等情况，问题要直接但不带攻击性。
- 文化匹配类：了解候选人的工作风格、协作偏好、对加班/不确定性/变化的态度，判断其与团队的融合度。

## 输出要求

每个问题需要包含：
- question: 问题本身（中文，口语化、自然，像真实面试官会说的话）
- purpose: 考察目的（中文，说明这个问题真正想测试什么）
- good_answer_elements: 优秀回答应包含的要素（中文数组）
- red_flags: 红旗信号（中文数组，具体描述什么样的回答暗示候选人可能不合适）

返回JSON格式：
{
  "opening": [1-2个开场问题，用于破冰并初步判断沟通表达能力],
  "experience_verification": [3-5个经历验证问题，STAR法+决策追问],
  "competency": [3-5个能力考察问题，情景题为主，至少1个需要当场分析/决策的压力题],
  "risk_probing": [1-3个风险探测问题，直击匹配分析中的风险点和简历疑点],
  "culture_fit": [1-2个文化匹配问题，了解工作风格和真实动机]
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
        highlights_text = "\n".join(f"- {h}" for h in match_highlights) if match_highlights else "- 无"
        risks_text = "\n".join(f"- {r}" for r in match_risks) if match_risks else "- 无"

        prompt = (
            f"## 岗位JD\n{jd_text}\n\n"
            f"## 候选人简历（已脱敏）\n{resume_text}\n\n"
            f"## 匹配分析亮点\n{highlights_text}\n\n"
            f"## 匹配分析风险\n{risks_text}"
        )
        prompt += format_criteria_section(
            preferences,
            "面试官自定义考察重点",
            "请确保生成的问题重点覆盖以上考察维度，高优先维度应有对应的经历验证题或能力考察题。",
        )

        data = await self._call_llm(prompt)
        return QuestionSet(
            opening=_parse_questions(data.get("opening", [])),
            experience_verification=_parse_questions(data.get("experience_verification", [])),
            competency=_parse_questions(data.get("competency", [])),
            risk_probing=_parse_questions(data.get("risk_probing", [])),
            culture_fit=_parse_questions(data.get("culture_fit", [])),
        )
