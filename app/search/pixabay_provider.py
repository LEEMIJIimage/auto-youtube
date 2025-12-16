import requests
from app.search.base import SearchProvider
from app.utils.config_loader import config
import logging

class PixabayProvider(SearchProvider):
    def __init__(self):
        self.logger = logging.getLogger("auto_youtube.image.pixabay")
        self.key = config.PIXABAY_API_KEY
        self.url = "https://pixabay.com/api/"

    def search(self, query: str) -> str:
        """단일 이미지 검색"""
        params = {
            "q": query,
            "key": self.key,
            "per_page": 3
        }

        if not self.key:
            return None

        try:
            r = requests.get(self.url, params=params, timeout=10)
            data = r.json()

            hits = data.get("hits")
            if hits:
                return hits[0]["largeImageURL"]
        except Exception as e:
            self.logger.exception("Pixabay API 오류: %s", e)

        return None
    
    def search_images(self, query: str, count: int = 4) -> list:
        """여러 이미지 검색 (ImageAggregator 호환)"""
        params = {
            "q": query,
            "key": self.key,
            "per_page": count
        }

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