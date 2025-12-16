from __future__ import annotations

from app.content.base import ContentItem, ContentProvider


class NaverNewsRSSProvider(ContentProvider):
    """
    Naver 뉴스 RSS/검색은 정책/엔드포인트가 자주 바뀌어서 템플릿으로 둡니다.
    - 원하는 소스(섹션 RSS, 검색 RSS 등)가 정해지면 여기 구현을 채우면 됩니다.
    """

    @property
    def name(self) -> str:
        return "rss_naver"

    def search(self, query: str, limit: int = 1):
        # TODO: Naver RSS/검색 소스 확정 후 구현
        return []


