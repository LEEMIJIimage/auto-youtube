import logging

import requests

from app.utils.config_loader import config


class UnsplashProvider:
    def __init__(self):
        self.logger = logging.getLogger("auto_youtube.image.unsplash")
        self.key = config.UNSPLASH_ACCESS_KEY
        self.url = "https://api.unsplash.com/search/photos"

    def search_images(self, query: str, count: int = 4) -> list[str]:
        params = {"query": query, "per_page": count, "client_id": self.key}

        if not self.key:
            return []

        try:
            r = requests.get(self.url, params=params, timeout=10)
            data = r.json()
            results = data.get("results", [])
            return [result["urls"]["regular"] for result in results[:count]]
        except Exception as e:
            self.logger.exception("Unsplash API 오류: %s", e)
            return []


