from typing import Optional

from app.utils.run_context import RunContext


class BasePipeline:
    def __init__(
        self,
        ai_provider,
        content_provider=None,
        image_provider=None,
        run_ctx: Optional[RunContext] = None,
        # backward compatibility
        search_provider=None,
    ):
        self.ai = ai_provider
        # 새 구조: self.content / self.images
        self.content = content_provider or search_provider
        self.images = image_provider
        self.run_ctx = run_ctx

    def run(self):
        raise NotImplementedError