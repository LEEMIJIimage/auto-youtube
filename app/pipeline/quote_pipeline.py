import logging
from datetime import datetime
from pathlib import Path

from app.content.aggregator import ContentAggregator
from app.content.reddit_provider import RedditProvider
from app.generator.quote_generator import generate_daily_quote_json
from app.pipeline.base_pipeline import BasePipeline
from app.short.quote_creator import create_quote_short
from app.utils.artifacts import save_json
from config import settings


class QuotePipeline(BasePipeline):
    """
    “하루 명언(명언모음집)” 숏츠만 생성하는 파이프라인
    - 배경: 검은색(이미지 검색 없음)
    - Reddit 글 -> OpenAI JSON -> typing effect video
    """

    @classmethod
    def build(cls, ai_provider, run_ctx):
        # RedditProvider: API키 없이 public JSON + seen 캐시/필터 포함(현재 구현 사용)
        reddit = RedditProvider(
            subreddits=list(settings.QUOTE_REDDIT_SUBREDDITS),
            min_text_len=200,
            allow_nsfw=False,
            output_dir=str(settings.OUTPUT_DIR),
        )
        content = ContentAggregator(providers=[reddit])
        return cls(ai_provider=ai_provider, content_provider=content, image_provider=None, run_ctx=run_ctx)

    def run(self):
        logger = logging.getLogger("auto_youtube.pipeline.quote")

        print("🔍 Reddit 포스트 랜덤 선택 중…")
        item = self.content.get_one(query=settings.QUOTE_REDDIT_QUERY)
        source = {
            "title": item.title,
            "summary": item.summary,
            "link": item.link,
            "source": item.source,
        }
        logger.info("source=%s", {k: source.get(k) for k in ("title", "link", "source")})

        print("🧠 OpenAI로 하루 명언 JSON 생성 중…")
        payload = generate_daily_quote_json(self.ai, source_title=source["title"], source_text=source["summary"], max_retries=2)

        # 아티팩트 저장(선택)
        if self.run_ctx:
            save_json(self.run_ctx.run_dir / "quote_payload.json", payload.__dict__)
            save_json(self.run_ctx.run_dir / "quote_source.json", source)

        print("🎬 명언 숏츠 영상 생성 중(타이핑 효과)…")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(settings.OUTPUT_DIR) / "shorts"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"quote_{ts}.mp4"

        token_interval = float(getattr(settings, "QUOTE_TOKEN_INTERVAL_SEC", 0.20))
        hold_sec = float(getattr(settings, "QUOTE_HOLD_SEC", 1.5))

        video_path = create_quote_short(
            video_title=payload.video_title,
            quote_lines=payload.quote_lines,
            typing_units=payload.typing_units,
            output_path=str(out_path),
            token_interval_sec=token_interval,
            hold_sec=hold_sec,
        )

        print("🎉 명언 숏츠 생성 완료!")
        print(f"결과: {video_path}")
        return video_path


