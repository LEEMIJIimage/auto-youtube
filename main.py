import logging

from app.ai.openai_provider import OpenAIProvider
from app.search.rss_provider import RSSProvider
from app.search.aggregator import ImageAggregator
from app.pipeline.crime_pipeline import CrimePipeline
from app.utils.logger import setup_logger
from app.utils.run_context import create_run_context
from config import settings

if __name__ == "__main__":
    level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)
    setup_logger("auto_youtube", level=level, force=True)

    run_ctx = create_run_context(settings.OUTPUT_DIR)

    ai = OpenAIProvider()
    search = RSSProvider()  # 뉴스 검색용
    images = ImageAggregator(run_ctx=run_ctx)  # 이미지 검색용

    pipeline = CrimePipeline(ai_provider=ai, search_provider=search, image_provider=images, run_ctx=run_ctx)
    pipeline.run()