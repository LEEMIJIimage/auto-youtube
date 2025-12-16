from __future__ import annotations

import logging
from typing import Sequence

from config import settings

from app.content.base import ContentItem, ContentProvider
from app.content.rss_google_provider import GoogleNewsRSSProvider
from app.content.rss_bbc_provider import BBCNewsRSSProvider
from app.content.rss_naver_provider import NaverNewsRSSProvider
from app.content.reddit_provider import RedditProvider


class ContentAggregator(ContentProvider):
    """
    여러 콘텐츠 소스 Provider를 우선순위대로 시도하는 Aggregator.
    """

    def __init__(self, providers: Sequence[ContentProvider] | None = None):
        self.logger = logging.getLogger("auto_youtube.content")

        if providers is not None:
            self.providers = list(providers)
        else:
            self.providers = self._build_from_settings()

        self.logger.info(
            "ContentAggregator providers=%s (priority=%s)",
            [p.name for p in self.providers],
            getattr(settings, "CONTENT_PROVIDER_PRIORITY", []),
        )

    @property
    def name(self) -> str:
        return "content_aggregator"

    def _build_from_settings(self) -> list[ContentProvider]:
        priority = list(getattr(settings, "CONTENT_PROVIDER_PRIORITY", ["rss_google"]))
        out: list[ContentProvider] = []

        for key in priority:
            if key == "rss_google":
                out.append(GoogleNewsRSSProvider())
            elif key == "rss_bbc":
                out.append(BBCNewsRSSProvider())
            elif key == "rss_naver":
                out.append(NaverNewsRSSProvider())
            elif key == "reddit":
                out.append(RedditProvider())

        # 최소한 하나는 보장
        if not out:
            out.append(GoogleNewsRSSProvider())
        return out

    def search(self, query: str, limit: int = 1):
        self.logger.info("search query=%r limit=%s", query, limit)
        for p in self.providers:
            try:
                self.logger.debug("provider_try=%s", p.name)
                items = list(p.search(query=query, limit=limit))
                self.logger.info("provider_ok=%s items=%s", p.name, len(items))
                if items:
                    return items
            except Exception as e:
                self.logger.exception("provider_fail=%s err=%s", p.name, e)
        self.logger.warning("all_content_providers_failed query=%r", query)
        return []

    def get_one(self, query: str) -> ContentItem:
        items = list(self.search(query=query, limit=1))
        if not items:
            raise RuntimeError(f"No content found by any provider query={query!r}")
        return items[0]


