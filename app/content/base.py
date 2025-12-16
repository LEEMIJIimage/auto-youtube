from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ContentItem:
    title: str
    summary: str
    link: str = ""
    source: str = ""


class ContentProvider(ABC):
    """
    스크립트 생성에 사용할 '텍스트 소스'를 제공하는 Provider 인터페이스.
    (이미지 provider와 완전히 분리)
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def search(self, query: str, limit: int = 1) -> Sequence[ContentItem]:
        """
        query로 소스를 찾아 ContentItem 리스트로 반환.
        """
        raise NotImplementedError

    def get_one(self, query: str) -> ContentItem:
        items = list(self.search(query=query, limit=1))
        if not items:
            raise RuntimeError(f"No content found by provider={self.name} query={query!r}")
        return items[0]


