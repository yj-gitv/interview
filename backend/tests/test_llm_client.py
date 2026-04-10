import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.services.llm_client import LLMClient


class TestLLMClient:
    def test_creates_with_config(self):
        client = LLMClient(
            api_key="test-key",
            base_url="https://test.com/v1",
        )
        assert client.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_chat_returns_text(self):
        client = LLMClient(api_key="test-key", base_url="https://test.com/v1")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.chat("Say hello", model="gpt-4o-mini")
            assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_chat_json_mode(self):
        json_str = '{"score": 85, "note": "Good match"}'
        client = LLMClient(api_key="test-key", base_url="https://test.com/v1")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json_str))]

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.chat_json(
                "Rate this", model="gpt-4o"
            )
            assert result["score"] == 85
