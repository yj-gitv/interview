from unittest.mock import AsyncMock, patch

import pytest

from app.services.matching import MatchingService, MatchResult


MOCK_LLM_RESPONSE = {
    "experience_score": 82,
    "experience_note": "3年产品经理经验，用户增长方向匹配度高",
    "industry_score": 75,
    "industry_note": "电商行业背景与目标岗位相关",
    "competency_score": 80,
    "competency_note": "数据分析和用户研究能力突出",
    "potential_score": 70,
    "potential_note": "学习能力强，但管理经验尚浅",
    "overall_score": 78,
    "recommendation": "推荐",
    "highlights": ["DAU提升60%的量化成果", "大厂经历"],
    "risks": ["跳槽频率偏高（2年一换）"],
}


class TestMatchingService:
    @pytest.mark.asyncio
    async def test_returns_match_result(self):
        service = MatchingService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.match(
                jd_text="招聘产品经理，负责用户增长",
                resume_text="3年产品经理经验，负责电商平台用户增长",
                preferences="",
            )
            assert isinstance(result, MatchResult)
            assert result.overall_score == 78
            assert result.recommendation == "推荐"
            assert len(result.highlights) >= 1
            assert len(result.risks) >= 1

    @pytest.mark.asyncio
    async def test_score_dimensions_are_in_range(self):
        service = MatchingService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.match(
                jd_text="JD text",
                resume_text="Resume text",
                preferences="",
            )
            for score in [
                result.experience_score,
                result.industry_score,
                result.competency_score,
                result.potential_score,
                result.overall_score,
            ]:
                assert 0 <= score <= 100


class TestMatchResultStructure:
    def test_match_result_fields(self):
        result = MatchResult(**MOCK_LLM_RESPONSE)
        assert result.experience_score == 82
        assert result.recommendation == "推荐"
