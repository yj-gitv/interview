from unittest.mock import AsyncMock, patch

import pytest

from app.services.question_gen import QuestionGenService, QuestionSet, Question


MOCK_LLM_RESPONSE = {
    "opening": [
        {
            "question": "请简单介绍一下你自己和最近这份工作的主要内容？",
            "purpose": "了解表达能力和自我认知",
            "good_answer_elements": ["结构清晰", "重点突出", "与岗位相关"],
            "red_flags": ["冗长散乱", "与简历出入大"],
        }
    ],
    "experience_verification": [
        {
            "question": "你提到DAU从500万提升到800万，能详细说说你具体做了什么吗？",
            "purpose": "验证核心经历真实性和深度",
            "good_answer_elements": ["STAR法则", "量化数据", "个人贡献清晰"],
            "red_flags": ["无法说出细节", "全是团队功劳"],
        }
    ],
    "competency": [
        {
            "question": "如果让你从零开始搭建一个用户增长体系，你会怎么做？",
            "purpose": "考察体系化思维和方法论",
            "good_answer_elements": ["分阶段规划", "数据驱动", "具体落地方案"],
            "red_flags": ["纸上谈兵", "缺乏逻辑"],
        }
    ],
    "risk_probing": [
        {
            "question": "看到你平均两年换一次工作，能说说每次离职的原因吗？",
            "purpose": "了解稳定性和职业规划",
            "good_answer_elements": ["坦诚", "有合理逻辑", "有长期规划"],
            "red_flags": ["甩锅", "回避"],
        }
    ],
    "culture_fit": [
        {
            "question": "你理想中的团队氛围是什么样的？",
            "purpose": "评估团队适配性",
            "good_answer_elements": ["具体描述", "有自知之明"],
            "red_flags": ["假大空"],
        }
    ],
}


class TestQuestionGenService:
    @pytest.mark.asyncio
    async def test_generates_question_set(self):
        service = QuestionGenService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.generate(
                jd_text="招聘产品经理",
                resume_text="3年产品经理经验",
                match_highlights=["DAU提升60%"],
                match_risks=["跳槽频繁"],
                preferences="",
            )
            assert isinstance(result, QuestionSet)
            assert len(result.opening) >= 1
            assert len(result.experience_verification) >= 1
            assert len(result.competency) >= 1
            assert isinstance(result.opening[0], Question)
            assert result.opening[0].question != ""
            assert result.opening[0].purpose != ""


class TestQuestionStructure:
    def test_question_has_all_fields(self):
        q = Question(
            question="测试问题",
            purpose="测试目的",
            good_answer_elements=["要素1"],
            red_flags=["红旗1"],
        )
        assert q.question == "测试问题"
        assert len(q.good_answer_elements) == 1
