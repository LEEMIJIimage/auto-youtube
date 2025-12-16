from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class ImageProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def search_images(self, query: str, count: int = 4) -> Sequence[str]:
        raise NotImplementedError


