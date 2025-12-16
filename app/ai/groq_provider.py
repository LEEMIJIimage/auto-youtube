# 향후 Groq API 적용 후 교체 가능
from app.ai.base import AIProvider

class GroqProvider(AIProvider):
    def generate_text(self, prompt: str) -> str:
        # TODO: Groq 모델 연결
        raise NotImplementedError