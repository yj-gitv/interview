import json

from openai import AsyncOpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.3,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def chat_json(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.1,
    ) -> dict:
        messages = []
        sys_msg = (system + "\n\n" if system else "") + "Respond with valid JSON only."
        messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or "{}"
        return json.loads(text)
