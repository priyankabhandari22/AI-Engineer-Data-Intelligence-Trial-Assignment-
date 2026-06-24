import asyncio
import json
import os
from loguru import logger
from google import genai as google_genai
from groq import Groq
from openai import AsyncOpenAI
import config.settings as settings


class LLMOrchestrator:
    def __init__(self):
        self.gemini_client = google_genai.Client(api_key=settings.GEMINI_API_KEY)
        self.groq = Groq(api_key=settings.GROQ_API_KEY)
        self.deepseek = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

    async def extract(self, text: str, schema_type: str) -> dict | None:
        prompt = self._build_prompt(text, schema_type)

        result = await self._try_gemini(prompt)
        if result:
            return result

        result = await self._try_groq(prompt)
        if result:
            return result

        result = await self._try_deepseek(prompt)
        return result

    async def _try_gemini(self, prompt: str) -> dict | None:
        for attempt in range(3):
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )
                return self._parse_json(response.text)
            except Exception as e:
                if "429" in str(e) or "503" in str(e) or "quota" in str(e).lower():
                    wait = (2 ** attempt) * 10
                    logger.warning(f"Gemini rate limited, waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Gemini error: {e}")
                    return None
        return None

    async def _try_groq(self, prompt: str) -> dict | None:
        for attempt in range(3):
            try:
                response = self.groq.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=1000,
                )
                return self._parse_json(response.choices[0].message.content)
            except Exception as e:
                if "429" in str(e):
                    wait = (2 ** attempt) * 5
                    logger.warning(f"Groq rate limited, waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Groq error: {e}")
                    return None
        return None

    async def _try_deepseek(self, prompt: str) -> dict | None:
        try:
            response = await self.deepseek.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1000,
            )
            return self._parse_json(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"DeepSeek error (all tiers failed): {e}")
            return None

    def _parse_json(self, text: str) -> dict | None:
        try:
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")
            return None

    def _build_prompt(self, text: str, schema_type: str) -> str:
        from .prompts import PROMPTS
        return PROMPTS[schema_type].format(text=text)
