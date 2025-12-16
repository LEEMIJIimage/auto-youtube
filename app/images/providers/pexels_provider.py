import logging

import requests

from app.utils.config_loader import config


class PexelsProvider:
    """Pexels 무료 이미지 검색 제공자"""

    def __init__(self):
        self.logger = logging.getLogger("auto_youtube.image.pexels")
        self.api_key = config.PEXELS_API_KEY
        self.base_url = "https://api.pexels.com/v1/search"

    def search_images(self, query, count=4):
        self.logger.info("search_images query=%r count=%s has_key=%s", query, count, bool(self.api_key))

        if not self.api_key:
            self.logger.warning("PEXELS_API_KEY empty -> using fallback images")
            return self._get_fallback_images(count)

        try:
            headers = {"Authorization": self.api_key}
            params = {
                "query": query,
                "per_page": count,
                "orientation": "landscape",
            }

            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            images = [photo["src"]["large"] for photo in data.get("photos", [])]

            if images:
                return images

            self.logger.warning("pexels returned 0 photos -> fallback")
            return self._get_fallback_images(count)
        except Exception as e:
            self.logger.exception("Pexels API 오류: %s", e)
            return self._get_fallback_images(count)

    def _get_fallback_images(self, count):
        fallback = [
            "https://images.pexels.com/photos/2280571/pexels-photo-2280571.jpeg",
            "https://images.pexels.com/photos/1181677/pexels-photo-1181677.jpeg",
            "https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg",
            "https://images.pexels.com/photos/1181673/pexels-photo-1181673.jpeg",
        ]
        return fallback[:count]


