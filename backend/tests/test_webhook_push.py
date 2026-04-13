from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.services.webhook_push import push_to_dingtalk, push_to_feishu, push_interview_result


class TestDingTalk:
    @pytest.mark.asyncio
    async def test_returns_false_when_no_url(self):
        with patch("app.services.webhook_push.settings") as mock_settings:
            mock_settings.dingtalk_webhook_url = ""
            result = await push_to_dingtalk("A", "PM", "推荐", "表现好")
            assert result is False

    @pytest.mark.asyncio
    async def test_sends_request_when_url_set(self):
        mock_response = MagicMock(status_code=200)
        with patch("app.services.webhook_push.settings") as mock_settings:
            mock_settings.dingtalk_webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=test"
            with patch("httpx.AsyncClient") as MockClient:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                MockClient.return_value = mock_client

                result = await push_to_dingtalk("候选人A", "产品经理", "推荐", "表现优秀")
                assert result is True
                mock_client.post.assert_called_once()


class TestFeishu:
    @pytest.mark.asyncio
    async def test_returns_false_when_no_url(self):
        with patch("app.services.webhook_push.settings") as mock_settings:
            mock_settings.feishu_webhook_url = ""
            result = await push_to_feishu("A", "PM", "推荐", "Good")
            assert result is False

    @pytest.mark.asyncio
    async def test_sends_request_when_url_set(self):
        mock_response = MagicMock(status_code=200)
        with patch("app.services.webhook_push.settings") as mock_settings:
            mock_settings.feishu_webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/test"
            with patch("httpx.AsyncClient") as MockClient:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                MockClient.return_value = mock_client

                result = await push_to_feishu("候选人B", "运营", "待定", "一般")
                assert result is True


class TestPushResult:
    @pytest.mark.asyncio
    async def test_dispatches_to_both(self):
        with patch("app.services.webhook_push.settings") as mock_settings:
            mock_settings.dingtalk_webhook_url = ""
            mock_settings.feishu_webhook_url = ""
            result = await push_interview_result("A", "PM", "推荐", "Good")
            assert result == {"dingtalk": False, "feishu": False}
