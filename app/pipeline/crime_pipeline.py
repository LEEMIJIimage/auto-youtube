from app.generator.script_generator import (
    generate_long_script,
    generate_short_script,
    clean_stage_directions,
)
from app.pipeline.base_pipeline import BasePipeline
from app.video.video_creator import create_long_video
from app.short.short_creator import create_short_video
from app.utils.artifacts import save_text, save_json
from config import settings
import logging

class CrimePipeline(BasePipeline):
    def run(self):
        logger = logging.getLogger("auto_youtube.pipeline.crime")
        print("🔍 뉴스 검색 중…")
        news = self.search.search()
        logger.info("news=%s", {k: news.get(k) for k in ("title", "link")})

        print("✍ 스크립트 생성 중…")
        long_script = generate_long_script(self.ai, news["title"], news["summary"])
        short_script = generate_short_script(self.ai, long_script)

        # 요구사항: 스크립트 txt 저장
        if self.run_ctx:
            save_json(self.run_ctx.run_dir / "news.json", news)
            save_text(self.run_ctx.scripts_dir / "long_script.txt", long_script)
            save_text(self.run_ctx.scripts_dir / "short_script.txt", short_script)
            logger.info("saved scripts/news to %s", self.run_ctx.run_dir)

        # 자막/영상용으로만 연출 지시문 제거 (RAW는 위에서 저장됨)
        long_script_display = clean_stage_directions(long_script)
        short_script_display = clean_stage_directions(short_script)

        print("🖼 이미지 검색 중…")
        images = self.images.search_images(news["title"], count=settings.LONG_IMAGE_COUNT)
        logger.info("images_found=%s first=%s", len(images) if images else 0, images[0] if images else None)

        print("🎬 롱폼 영상 제작 중…")
        long_out = str(self.run_ctx.run_dir / settings.LONG_VIDEO_FILENAME) if self.run_ctx else None
        long_video = create_long_video(long_script_display, images, output_path=long_out)

        print("🎞 숏츠 제작 중…")
        short_out = str(self.run_ctx.run_dir / settings.SHORT_VIDEO_FILENAME) if self.run_ctx else None
        short_images = images[: settings.SHORT_IMAGE_COUNT] if images else ["https://via.placeholder.com/1080x1920/111111/ffffff?text=No+Images"]
        short_video = create_short_video(short_script_display, short_images, output=short_out)

        print("🎉 파이프라인 완료!")
        print(f"롱폼 영상: {long_video}")
        print(f"숏츠 영상: {short_video}")
        return long_video, short_video