import feedparser
from urllib.parse import quote_plus
from app.search.base import SearchProvider
from config import settings
import logging

class RSSProvider(SearchProvider):
    def __init__(self, query=None, hl="ko", gl="KR", ceid="KR:ko"):
        self.logger = logging.getLogger("auto_youtube.news.rss")
        if query is None:
            query = settings.DEFAULT_NEWS_QUERY
        encoded_query = quote_plus(query)  # 공백 -> +, 한글 안전 인코딩
        self.url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"

    def search(self):
        self.logger.info("news_search url=%s", self.url)
        feed = feedparser.parse(self.url)

        # 구글뉴스 RSS가 실패해도 entries가 비어있을 수 있어 디버깅 정보를 남기면 좋음
        if not feed.entries:
            # feed.bozo: 파싱 에러가 있었는지 여부
            reason = getattr(feed, "bozo_exception", None)
            self.logger.error("no_news bozo=%s reason=%r", getattr(feed, "bozo", None), reason)
            raise Exception(f"No news found (url={self.url}, bozo={getattr(feed,'bozo',None)}, reason={reason})")

        entry = feed.entries[0]
        item = {
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "link": entry.get("link", "")
        }
        self.logger.info("news_ok title=%r link=%r", item["title"], item["link"])
        return item