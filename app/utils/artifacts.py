from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def download_image_to(path: Path, url: str, timeout: int = 15) -> bool:
    """
    url 이미지를 다운로드해서 path에 저장. 성공하면 True.
    """
    logger = logging.getLogger("auto_youtube.artifacts")
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "auto-youtube/1.0"})
        r.raise_for_status()
        path.write_bytes(r.content)
        logger.debug("image_saved url=%s path=%s bytes=%s", url, path, len(r.content))
        return True
    except Exception as e:
        logger.exception("image_save_fail url=%s path=%s err=%s", url, path, e)
        return False


