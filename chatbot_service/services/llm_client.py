import asyncio
import backoff
import logging
from openai import OpenAI, AsyncOpenAI
from fastapi import Depends

from config import settings

logger = logging.getLogger("llm_client")


class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger("llm_client")

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        giveup=lambda e: "content_filter" in str(e).lower(),
    )
    async def complete(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000
    ) -> str:
        """
        Gửi prompt đến LLM và nhận phản hồi
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {str(e)}")
            raise

    async def complete_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Gửi prompt với system instruction
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API with system prompt: {str(e)}")
            raise


# Dependency
def get_llm_client() -> LLMClient:
    return LLMClient(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
