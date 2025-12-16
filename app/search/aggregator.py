from app.search.pexels_provider import PexelsProvider
from app.search.unsplash_provider import UnsplashProvider
from app.search.pixabay_provider import PixabayProvider
from app.utils.config_loader import config
from app.utils.artifacts import download_image_to
from app.utils.run_context import RunContext
from config import settings
import logging


class ImageAggregator:
    """여러 이미지 제공자를 통합하는 클래스"""
    
    def __init__(self, run_ctx: RunContext | None = None):
        self.logger = logging.getLogger("auto_youtube.image")
        self.run_ctx = run_ctx
        self.providers = []
        
        # 설정된 우선순위에 따라 제공자 초기화
        for provider_name in settings.IMAGE_PROVIDER_PRIORITY:
            if provider_name == "pexels" and config.PEXELS_API_KEY:
                self.providers.append(PexelsProvider())
            elif provider_name == "unsplash" and config.UNSPLASH_ACCESS_KEY:
                self.providers.append(UnsplashProvider())
            elif provider_name == "pixabay" and config.PIXABAY_API_KEY:
                self.providers.append(PixabayProvider())
        
        # 기본 제공자가 없으면 Pexels 추가
        if not self.providers:
            self.providers.append(PexelsProvider())

        self.logger.info(
            "ImageAggregator providers=%s (priority=%s)",
            [p.__class__.__name__ for p in self.providers],
            settings.IMAGE_PROVIDER_PRIORITY,
        )
    
    def search_images(self, query, count=4):
        """
        여러 제공자를 통해 이미지 검색
        
        Args:
            query: 검색어
            count: 이미지 개수
            
        Returns:
            list: 이미지 URL 목록
        """
        self.logger.info("search_images query=%r count=%s", query, count)

        saved_paths: list[str] = []

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                self.logger.debug("provider_try=%s", provider_name)
                urls = provider.search_images(query, count)
                self.logger.info("provider_ok=%s urls=%s", provider_name, len(urls) if urls else 0)

                # 요구사항: "사진 하나 찾을때마다 run 폴더에 저장"
                if urls:
                    for idx, url in enumerate(urls[:count]):
                        if self.run_ctx:
                            # 확장자 힌트가 없을 수도 있어 .jpg로 통일
                            filename = f"{provider_name.lower()}_{idx+1:02d}.jpg"
                            out_path = self.run_ctx.images_dir / filename
                            ok = download_image_to(out_path, url)
                            if ok:
                                saved_paths.append(str(out_path))
                                self.logger.info("image_saved provider=%s idx=%s path=%s", provider_name, idx, out_path)
                            else:
                                self.logger.warning("image_save_failed provider=%s idx=%s url=%s", provider_name, idx, url)
                        else:
                            # run_ctx가 없으면 URL 그대로 반환
                            saved_paths.append(url)

                    if saved_paths:
                        return saved_paths[:count]
            except Exception as e:
                self.logger.exception("provider_fail=%s err=%s", provider_name, e)
                continue
        
        # 모든 제공자가 실패하면 기본 이미지 반환
        self.logger.warning("all_providers_failed: using default placeholder images")
        return self._get_default_images(count)
    
    def _get_default_images(self, count):
        """기본 이미지 반환"""
        default = [
            "https://via.placeholder.com/800x600/333333/ffffff?text=Image+1",
            "https://via.placeholder.com/800x600/444444/ffffff?text=Image+2", 
            "https://via.placeholder.com/800x600/555555/ffffff?text=Image+3",
            "https://via.placeholder.com/800x600/666666/ffffff?text=Image+4",
        ]
        return default[:count]