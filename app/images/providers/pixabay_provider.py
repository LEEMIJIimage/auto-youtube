import logging

import requests

from app.utils.config_loader import config


class PixabayProvider:
    def __init__(self):
        self.logger = logging.getLogger("auto_youtube.image.pixabay")
        self.key = config.PIXABAY_API_KEY
        self.url = "https://pixabay.com/api/"

    def search_images(self, query: str, count: int = 4) -> list[str]:
        params = {"q": query, "key": self.key, "per_page": count}

        if not self.key:
            return []

        try:
            r = requests.get(self.url, params=params, timeout=10)
            data = r.json()
            hits = data.get("hits", [])
            return [hit["largeImageURL"] for hit in hits[:count]]
        except Exception as e:
            self.logger.exception("Pixabay API 오류: %s", e)
            return []


