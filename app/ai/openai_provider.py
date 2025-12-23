from openai import OpenAI
from app.ai.base import AIProvider
from app.utils.config_loader import config
from config import settings
import json

class OpenAIProvider(AIProvider):
    def __init__(self):
        # config에서 이미 required=True로 검증됨
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_text(self, prompt: str) -> str:
        res = self.client.chat.completions.create(
            model=getattr(settings, "AI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=getattr(settings, "AI_TEMPERATURE", 0.7),
            max_tokens=getattr(settings, "AI_MAX_TOKENS", 1200),
        )
        return res.choices[0].message.content

    def generate_json(self, prompt: str) -> dict:
        """
        JSON만 반환하도록 강제(response_format=json_object)하고 dict로 파싱.
        """
        res = self.client.chat.completions.create(
            model=getattr(settings, "AI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=getattr(settings, "AI_TEMPERATURE", 0.7),
            max_tokens=getattr(settings, "AI_MAX_TOKENS", 1200),
            response_format={"type": "json_object"},
        )
        raw = res.choices[0].message.content or "{}"
        return json.loads(raw)