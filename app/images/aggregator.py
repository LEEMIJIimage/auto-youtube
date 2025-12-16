from __future__ import annotations

import logging
from typing import Sequence

from config import settings

from app.utils.artifacts import download_image_to
from app.utils.run_context import RunContext

from app.images.providers.pexels_provider import PexelsProvider
from app.images.providers.unsplash_provider import UnsplashProvider
from app.images.providers.pixabay_provider import PixabayProvider


class ImageAggregator:
    """
    이미지 provider를 우선순위대로 시도하는 Aggregator.
    """

    def __init__(self, run_ctx: RunContext | None = None):
        self.logger = logging.getLogger("auto_youtube.image")
        self.run_ctx = run_ctx
        self.providers = []

        for provider_name in settings.IMAGE_PROVIDER_PRIORITY:
            if provider_name == "pexels":
                self.providers.append(PexelsProvider())
            elif provider_name == "unsplash":
                self.providers.append(UnsplashProvider())
            elif provider_name == "pixabay":
                self.providers.append(PixabayProvider())

        if not self.providers:
            self.providers.append(PexelsProvider())

        self.logger.info(
            "ImageAggregator providers=%s (priority=%s)",
            [p.__class__.__name__ for p in self.providers],
            settings.IMAGE_PROVIDER_PRIORITY,
        )

    def search_images(self, query: str, count: int = 4) -> list[str]:
        self.logger.info("search_images query=%r count=%s", query, count)
        saved_paths: list[str] = []

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                self.logger.debug("provider_try=%s", provider_name)
                urls = provider.search_images(query, count)
                self.logger.info("provider_ok=%s urls=%s", provider_name, len(urls) if urls else 0)

                if urls:
                    for idx, url in enumerate(urls[:count]):
                        if self.run_ctx:
                            filename = f"{provider_name.lower()}_{idx+1:02d}.jpg"
                            out_path = self.run_ctx.images_dir / filename
                            ok = download_image_to(out_path, url)
                            if ok:
                                saved_paths.append(str(out_path))
                            else:
                                self.logger.warning("image_save_failed provider=%s idx=%s url=%s", provider_name, idx, url)
                        else:
                            saved_paths.append(url)

                    if saved_paths:
                        return saved_paths[:count]
            except Exception as e:
                self.logger.exception("provider_fail=%s err=%s", provider_name, e)

        self.logger.warning("all_providers_failed: using default placeholder images")
        return self._get_default_images(count)

    def _get_default_images(self, count: int) -> list[str]:
        default = [
            "https://via.placeholder.com/800x600/333333/ffffff?text=Image+1",
            "https://via.placeholder.com/800x600/444444/ffffff?text=Image+2",
            "https://via.placeholder.com/800x600/555555/ffffff?text=Image+3",
            "https://via.placeholder.com/800x600/666666/ffffff?text=Image+4",
        ]
        return default[:count]


