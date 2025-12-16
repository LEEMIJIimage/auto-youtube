from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

import requests

from app.content.base import ContentItem, ContentProvider


@dataclass
class RedditPost:
    title: str
    selftext: str
    permalink: str
    score: int
    num_comments: int
    created_utc: int
    subreddit: str
    is_nsfw: bool


class RedditProvider(ContentProvider):
    """
    Reddit 콘텐츠 Provider (API key 없이 public JSON 사용)
    - subreddits에서 search.json으로 검색
    - 중복 방지(seen 파일)
    - 간단한 필터링(NSFW, 너무 짧은 글 등)
    """

    def __init__(
        self,
        subreddits: list[str] | None = None,
        *,
        fetch_limit: int = 30,
        seen_ttl_sec: int = 60 * 60 * 24 * 7,  # 7일
        seen_file: str = "seen_reddit.json",
        output_dir: str | None = None,
        min_text_len: int = 200,
        allow_nsfw: bool = False,
        user_agent: str = "auto-youtube/1.0 (by u/auto_youtube_bot)",
        timeout_sec: int = 15,
    ):
        self.logger = logging.getLogger("auto_youtube.content.reddit")
        self.subreddits = subreddits or ["TrueCrime", "UnresolvedMysteries", "MorbidReality"]
        self.fetch_limit = max(10, int(fetch_limit))
        self.seen_ttl_sec = int(seen_ttl_sec)
        self.min_text_len = int(min_text_len)
        self.allow_nsfw = bool(allow_nsfw)
        self.user_agent = user_agent
        self.timeout_sec = int(timeout_sec)

        base_dir = Path(output_dir) if output_dir else Path(getattr(__import__("config").settings, "OUTPUT_DIR", "."))
        self.seen_path = base_dir / seen_file

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent})

    @property
    def name(self) -> str:
        return "reddit"

    def _load_seen(self) -> dict[str, int]:
        if not self.seen_path.exists():
            return {}
        try:
            return json.loads(self.seen_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_seen(self, seen: dict[str, int]) -> None:
        self.seen_path.parent.mkdir(parents=True, exist_ok=True)
        self.seen_path.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")

    def _prune_seen(self, seen: dict[str, int]) -> dict[str, int]:
        now = int(time.time())
        return {k: int(v) for k, v in seen.items() if (now - int(v)) < self.seen_ttl_sec}

    def _fetch_posts(self, subreddit: str, query: str) -> list[RedditPost]:
        # Reddit search endpoint (public)
        # sort=relevance/new/hot 등을 바꿔도 됨
        q = quote_plus(query)
        url = (
            f"https://www.reddit.com/r/{subreddit}/search.json"
            f"?q={q}&restrict_sr=1&sort=new&t=week&limit={self.fetch_limit}"
        )

        self.logger.info("fetch subreddit=%s url=%s", subreddit, url)

        r = self._session.get(url, timeout=self.timeout_sec)
        r.raise_for_status()
        data = r.json()

        children = (((data or {}).get("data") or {}).get("children") or [])
        out: list[RedditPost] = []
        for c in children:
            d = (c or {}).get("data") or {}
            title = d.get("title") or ""
            selftext = d.get("selftext") or ""
            permalink = d.get("permalink") or ""
            if not permalink:
                continue

            out.append(
                RedditPost(
                    title=title,
                    selftext=selftext,
                    permalink="https://www.reddit.com" + permalink,
                    score=int(d.get("score") or 0),
                    num_comments=int(d.get("num_comments") or 0),
                    created_utc=int(d.get("created_utc") or 0),
                    subreddit=str(d.get("subreddit") or subreddit),
                    is_nsfw=bool(d.get("over_18") or False),
                )
            )
        return out

    def _filter_posts(self, posts: Iterable[RedditPost]) -> list[RedditPost]:
        filtered: list[RedditPost] = []
        for p in posts:
            if (not self.allow_nsfw) and p.is_nsfw:
                continue

            # 제목만 있고 본문이 거의 없는 글은 영상화가 힘듦
            if len((p.selftext or "").strip()) < self.min_text_len:
                continue

            filtered.append(p)
        return filtered

    def search(self, query: str, limit: int = 1):
        limit = max(1, int(limit))
        seen = self._prune_seen(self._load_seen())

        all_posts: list[RedditPost] = []
        for sr in self.subreddits:
            try:
                posts = self._fetch_posts(sr, query)
                all_posts.extend(posts)
            except Exception as e:
                self.logger.exception("fetch_fail subreddit=%s err=%s", sr, e)

        if not all_posts:
            self.logger.warning("no_posts query=%r", query)
            return []

        # 1) 필터링
        candidates = self._filter_posts(all_posts)

        # 2) 중복 제거 (permalink 기준)
        #    + seen 제거
        uniq: dict[str, RedditPost] = {}
        for p in candidates:
            uniq[p.permalink] = p
        candidates = list(uniq.values())

        fresh = [p for p in candidates if p.permalink not in seen]
        pool = fresh if fresh else candidates

        # 3) “좋은 글”을 약간 우선시: 점수+댓글 가중치로 상위 일부 추리기
        pool.sort(key=lambda x: (x.score * 2 + x.num_comments), reverse=True)
        top = pool[: min(len(pool), 15)]  # 상위 15개 안에서 랜덤
        random.shuffle(top)

        chosen_posts = top[:limit]

        # 4) seen 기록
        now = int(time.time())
        for p in chosen_posts:
            seen[p.permalink] = now
        self._save_seen(seen)

        items: list[ContentItem] = []
        for p in chosen_posts:
            # summary는 selftext 앞부분만 (너의 스크립트 생성 단계에서 다시 요약/재구성할 거니까)
            summary = (p.selftext or "").strip()
            if len(summary) > 1200:
                summary = summary[:1200] + "..."

            items.append(
                ContentItem(
                    title=p.title,
                    summary=summary,
                    link=p.permalink,
                    source=self.name,
                )
            )

        self.logger.info(
            "ok items=%s fresh=%s/%s first_title=%r",
            len(items),
            len(fresh),
            len(candidates),
            items[0].title if items else "",
        )
        return items