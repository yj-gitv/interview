from unittest.mock import AsyncMock, patch

import pytest

from app.services.realtime_analysis import RealtimeAnalysisService, AnalysisResult


SAMPLE_QUESTIONS = [
    {"question": "请做自我介绍", "purpose": "了解表达", "good_answer_elements": ["结构清晰"], "red_flags": ["冗长"]},
    {"question": "说说你的项目经验", "purpose": "验证经历", "good_answer_elements": ["STAR法则"], "red_flags": ["无细节"]},
]

MOCK_ANALYSIS = {
    "current_question_index": 0,
    "elements_checked": ["结构清晰"],
    "follow_up_suggestions": ["能否举一个具体的数据指标来说明你的成果？"],
    "instant_rating": "好",
    "instant_comment": "表达清晰有条理",
}


class TestRealtimeAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_returns_result(self):
        service = RealtimeAnalysisService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_ANALYSIS
        ):
            result = await service.analyze(
                transcript_so_far="面试官：请做自我介绍\n候选人：我是张三，有3年产品经理经验...",
                questions=SAMPLE_QUESTIONS,
                current_question_index=0,
            )
            assert isinstance(result, AnalysisResult)
            assert result.current_question_index == 0
            assert len(result.follow_up_suggestions) >= 1

    @pytest.mark.asyncio
    async def test_detects_question_switch(self):
        mock_response = {
            "current_question_index": 1,
            "elements_checked": [],
            "follow_up_suggestions": [],
            "instant_rating": "",
            "instant_comment": "",
        }
        service = RealtimeAnalysisService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await service.analyze(
                transcript_so_far="面试官：说说你的项目经验\n候选人：我之前做过...",
                questions=SAMPLE_QUESTIONS,
                current_question_index=0,
            )
            assert result.current_question_index == 1


class TestAnalysisResult:
    def test_fields(self):
        result = AnalysisResult(**MOCK_ANALYSIS)
        assert result.instant_rating == "好"
        assert "数据指标" in result.follow_up_suggestions[0]
