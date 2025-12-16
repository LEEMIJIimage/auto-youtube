from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path
from urllib.parse import quote_plus

import feedparser

from app.content.base import ContentItem, ContentProvider


class GoogleNewsRSSProvider(ContentProvider):
    """
    Google News RSS 검색 기반 콘텐츠 소스.
    - 같은 기사만 반복되는 문제 방지:
      1) 상위 fetch_limit개를 가져오고
      2) 최근 seen(캐시)에 있는 link는 제외
      3) 남은 후보에서 랜덤(또는 가중치) 선택
    """

    def __init__(
        self,
        hl: str = "ko",
        gl: str = "KR",
        ceid: str = "KR:ko",
        *,
        fetch_limit: int = 40,
        seen_ttl_sec: int = 60 * 60 * 24,  # 24h
        seen_file: str = "seen_rss_google.json",
        output_dir: str | None = None,
    ):
        self._hl = hl
        self._gl = gl
        self._ceid = ceid
        self._fetch_limit = max(5, int(fetch_limit))
        self._seen_ttl_sec = int(seen_ttl_sec)
        self.logger = logging.getLogger("auto_youtube.content.rss_google")

        base_dir = Path(output_dir) if output_dir else Path(getattr(__import__("config").settings, "OUTPUT_DIR", "."))
        self._seen_path = (base_dir / seen_file)

    @property
    def name(self) -> str:
        return "rss_google"

    def _build_url(self, query: str) -> str:
        encoded = quote_plus(query)
        return f"https://news.google.com/rss/search?q={encoded}&hl={self._hl}&gl={self._gl}&ceid={self._ceid}"

    def _load_seen(self) -> dict[str, int]:
        if not self._seen_path.exists():
            return {}
        try:
            return json.loads(self._seen_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_seen(self, seen: dict[str, int]) -> None:
        self._seen_path.parent.mkdir(parents=True, exist_ok=True)
        self._seen_path.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")

    def _prune_seen(self, seen: dict[str, int]) -> dict[str, int]:
        now = int(time.time())
        return {k: int(v) for k, v in seen.items() if (now - int(v)) < self._seen_ttl_sec}

    def search(self, query: str, limit: int = 1):
        url = self._build_url(query)
        limit = max(1, int(limit))

        self.logger.info("search url=%s limit=%s fetch_limit=%s", url, limit, self._fetch_limit)
        feed = feedparser.parse(url)

        entries = getattr(feed, "entries", None) or []
        if not entries:
            reason = getattr(feed, "bozo_exception", None)
            self.logger.error("no_entries bozo=%s reason=%r", getattr(feed, "bozo", None), reason)
            return []

        # 1) 후보를 넉넉히 뽑는다 (항상 0번만 쓰지 않도록)
        raw_candidates: list[ContentItem] = []
        for entry in entries[: self._fetch_limit]:
            title = entry.get("title", "") or ""
            link = entry.get("link", "") or ""
            summary = entry.get("summary", "") or ""

            if not title or not link:
                continue

            raw_candidates.append(
                ContentItem(
                    title=title,
                    summary=summary,
                    link=link,
                    source=self.name,
                )
            )

        if not raw_candidates:
            self.logger.error("no_usable_candidates")
            return []

        # 2) 최근 사용한 링크 제외
        seen = self._prune_seen(self._load_seen())
        fresh = [c for c in raw_candidates if c.link not in seen]

        # 3) 고정 상단 반복 방지: fresh가 있으면 fresh에서, 없으면 raw에서
        pool = fresh if fresh else raw_candidates

        # 4) 랜덤 선택 (원하면 여기서 가중치 전략으로 바꿀 수도 있음)
        random.shuffle(pool)
        chosen = pool[:limit]

        # 5) 선택된 링크를 seen에 기록
        now = int(time.time())
        for c in chosen:
            seen[c.link] = now
        self._save_seen(seen)

        self.logger.info(
            "ok items=%s fresh=%s/%s first_title=%r",
            len(chosen),
            len(fresh),
            len(raw_candidates),
            chosen[0].title if chosen else "",
        )
        return chosen