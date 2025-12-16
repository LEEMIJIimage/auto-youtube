import logging

from app.content.aggregator import ContentAggregator
from app.content.reddit_provider import RedditProvider
from app.images.aggregator import ImageAggregator
from app.generator.script_generator import (
    clean_stage_directions,
    generate_humor_long_script,
    generate_humor_short_script,
)
from app.pipeline.base_pipeline import BasePipeline
from app.short.short_creator import create_short_video
from app.utils.artifacts import save_json, save_text
from app.video.video_creator import create_long_video
from config import settings


class HumorPipeline(BasePipeline):
    """
    RedditProvider 기반 유머 파이프라인
    - content: Reddit에서 글을 가져옴
    - images: 제목 기반으로 이미지 검색/저장
    - ai: 한국어 유머 스크립트 생성
    """

    @classmethod
    def build(cls, ai_provider, run_ctx):
        # 유머는 Reddit 기반으로 강제 (원하면 settings.CONTENT_PROVIDER_PRIORITY로도 확장 가능)
        content = ContentAggregator(
            providers=[RedditProvider(subreddits=list(settings.HUMOR_REDDIT_SUBREDDITS), min_text_len=50)]
        )
        images = ImageAggregator(run_ctx=run_ctx)
        return cls(ai_provider=ai_provider, content_provider=content, image_provider=images, run_ctx=run_ctx)

    def run(self):
        logger = logging.getLogger("auto_youtube.pipeline.humor")

        print("🔍 Reddit 유머 콘텐츠 검색 중…")
        item = self.content.get_one(query=settings.HUMOR_QUERY)
        content = {
            "title": item.title,
            "summary": item.summary,
            "link": item.link,
            "source": item.source,
        }
        logger.info("content=%s", {k: content.get(k) for k in ("title", "link", "source")})

        print("✍ 유머 스크립트 생성 중…")
        long_script = generate_humor_long_script(self.ai, content["title"], content["summary"])
        short_script = generate_humor_short_script(self.ai, long_script)

        if self.run_ctx:
            save_json(self.run_ctx.run_dir / "content.json", content)
            save_text(self.run_ctx.scripts_dir / "long_script.txt", long_script)
            save_text(self.run_ctx.scripts_dir / "short_script.txt", short_script)
            logger.info("saved scripts/content to %s", self.run_ctx.run_dir)

        long_script_display = clean_stage_directions(long_script)
        short_script_display = clean_stage_directions(short_script)

        print("🖼 이미지 검색 중…")
        images = self.images.search_images(content["title"], count=settings.LONG_IMAGE_COUNT)
        logger.info("images_found=%s first=%s", len(images) if images else 0, images[0] if images else None)

        # print("🎬 롱폼 영상 제작 중…")
        # long_out = str(self.run_ctx.run_dir / settings.LONG_VIDEO_FILENAME) if self.run_ctx else None
        # long_video = create_long_video(long_script_display, images, output_path=long_out)

        print("🎞 숏츠 제작 중…")
        short_out = str(self.run_ctx.run_dir / settings.SHORT_VIDEO_FILENAME) if self.run_ctx else None
        short_images = images[: settings.SHORT_IMAGE_COUNT] if images else []
        if not short_images:
            short_images = ["https://via.placeholder.com/1080x1920/111111/ffffff?text=No+Images"]
        short_video = create_short_video(short_script_display, short_images, output=short_out)

        print("🎉 유머 파이프라인 완료!")
        # print(f"롱폼 영상: {long_video}")
        print(f"숏츠 영상: {short_video}")
        # return long_video, short_video


