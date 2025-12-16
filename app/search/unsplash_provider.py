import requests
from app.search.base import SearchProvider
from app.utils.config_loader import config
import logging

class UnsplashProvider(SearchProvider):
    def __init__(self):
        self.logger = logging.getLogger("auto_youtube.image.unsplash")
        self.key = config.UNSPLASH_ACCESS_KEY
        self.url = "https://api.unsplash.com/search/photos"

    def search(self, query: str) -> str:
        """단일 이미지 검색"""
        params = {
            "query": query,
            "per_page": 1,
            "client_id": self.key
        }
        
        if not self.key:
            return None

        try:
            r = requests.get(self.url, params=params, timeout=10)
            data = r.json()

            if data.get("results"):
                return data["results"][0]["urls"]["regular"]
        except Exception as e:
            self.logger.exception("Unsplash API 오류: %s", e)

        return None
    
    def search_images(self, query: str, count: int = 4) -> list:
        """여러 이미지 검색 (ImageAggregator 호환)"""
        params = {
            "query": query,
            "per_page": count,
            "client_id": self.key
        }
        
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