from __future__ import annotations

import logging

import feedparser

from app.content.base import ContentItem, ContentProvider


class BBCNewsRSSProvider(ContentProvider):
    """
    BBC RSS 기반 템플릿 Provider.
    - 실제 쿼리 검색은 BBC RSS가 제한적이어서, 키워드 필터링 방식으로 확장하는 것을 권장.
    """

    def __init__(self, feed_url: str = "https://feeds.bbci.co.uk/news/rss.xml"):
        self.feed_url = feed_url
        self.logger = logging.getLogger("auto_youtube.content.rss_bbc")

    @property
    def name(self) -> str:
        return "rss_bbc"

    def search(self, query: str, limit: int = 1):
        self.logger.info("search feed=%s query=%r limit=%s", self.feed_url, query, limit)
        feed = feedparser.parse(self.feed_url)
        if not getattr(feed, "entries", None):
            return []

        q = (query or "").lower()
        out = []
        for entry in feed.entries:
            title = (entry.get("title", "") or "")
            summary = (entry.get("summary", "") or "")
            if q and (q not in title.lower()) and (q not in summary.lower()):
                continue
            out.append(
                ContentItem(
                    title=title,
                    summary=summary,
                    link=entry.get("link", ""),
                    source=self.name,
                )
            )
            if len(out) >= max(1, limit):
                break
        self.logger.info("ok items=%s", len(out))
        return out


