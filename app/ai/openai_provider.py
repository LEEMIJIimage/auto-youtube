from openai import OpenAI
from app.ai.base import AIProvider
from app.utils.config_loader import config

class OpenAIProvider(AIProvider):
    def __init__(self):
        # config에서 이미 required=True로 검증됨
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_text(self, prompt: str) -> str:
        res = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return res.choices[0].message.content