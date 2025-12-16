from pathlib import Path
from typing import Optional

from app.utils.run_context import RunContext


class BasePipeline:
    def __init__(self, ai_provider, search_provider, image_provider, run_ctx: Optional[RunContext] = None):
        self.ai = ai_provider
        self.search = search_provider
        self.images = image_provider
        self.run_ctx = run_ctx

    def run(self):
        raise NotImplementedError