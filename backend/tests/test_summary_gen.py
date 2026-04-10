from unittest.mock import AsyncMock, patch

import pytest

from app.services.summary_gen import SummaryGenService, SummaryResult


MOCK_LLM_RESPONSE = {
    "candidate_overview": "候选人具有3年产品经理经验，在用户增长方向有突出表现。",
    "expression_score": 85,
    "case_richness_score": 78,
    "depth_score": 80,
    "self_awareness_score": 72,
    "enthusiasm_score": 88,
    "overall_score": 81,
    "highlights": ["数据驱动思维强", "表达逻辑清晰", "有量化成果"],
    "concerns": ["管理经验不足", "对行业趋势了解有限"],
    "jd_alignment": [
        {"requirement": "用户增长经验", "status": "达成", "note": "有直接DAU提升经验"},
        {"requirement": "团队管理", "status": "部分达成", "note": "带过2人小团队"},
    ],
    "recommendation": "推荐",
    "recommendation_reason": "核心能力与岗位需求匹配度高，虽然管理经验需要培养，但成长潜力好。",
    "next_steps": "建议二面重点考察团队管理能力和跨部门协作经验。",
}


class TestSummaryGenService:
    @pytest.mark.asyncio
    async def test_generates_summary(self):
        service = SummaryGenService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.generate(
                transcript="面试官：请自我介绍\n候选人：我是一名产品经理...",
                jd_text="招聘产品经理",
                resume_text="3年经验",
                match_data={"overall_score": 78, "highlights": ["经验丰富"]},
            )
            assert isinstance(result, SummaryResult)
            assert result.overall_score == 81
            assert result.recommendation == "推荐"
            assert len(result.highlights) >= 1
            assert len(result.jd_alignment) >= 1


class TestSummaryResult:
    def test_fields(self):
        result = SummaryResult(**MOCK_LLM_RESPONSE)
        assert result.candidate_overview != ""
        assert result.expression_score == 85
