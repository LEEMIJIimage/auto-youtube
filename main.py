import logging
import argparse

from app.ai.openai_provider import OpenAIProvider
from app.pipeline.loader import load_pipeline_class
from app.utils.logger import setup_logger
from app.utils.run_context import create_run_context
from config import settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", default="crime")
    args = parser.parse_args()

    level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)
    setup_logger("auto_youtube", level=level, force=True)

    run_ctx = create_run_context(settings.OUTPUT_DIR)

    ai = OpenAIProvider()

    PipelineCls = load_pipeline_class(args.pipeline)
    pipeline = PipelineCls.build(ai_provider=ai, run_ctx=run_ctx)
    pipeline.run()