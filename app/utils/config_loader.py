# app/utils/config_loader.py

import os
from pathlib import Path
from dotenv import load_dotenv


def _load_env() -> None:
    """
    .env 로딩을 코드에서 보장.
    (VS Code/Cursor의 terminal env injection 설정이 꺼져 있어도 동작)
    """
    project_root = Path(__file__).resolve().parents[2]  # auto-youtube/
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_env()


def get_env(key: str, default=None, required: bool = False) -> str:
    value = os.getenv(key, default)
    if required and (value is None or value == ""):
        raise ValueError(f"환경변수 '{key}'가 설정되어 있지 않습니다.")
    return value


def get_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "y", "on")


def get_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ValueError(f"환경변수 '{key}'는 int 여야 합니다. 현재 값: {raw}") from e


class Config:
    """
    '환경변수 스펙'을 한 곳에 모아두는 클래스.
    - 필수/옵션을 명확히
    - 기본값/타입 변환을 일관되게
    """

    # Secrets / API Keys
    OPENAI_API_KEY: str = get_env("OPENAI_API_KEY", required=True)
    UNSPLASH_ACCESS_KEY: str = get_env("UNSPLASH_ACCESS_KEY", default="")
    PEXELS_API_KEY: str = get_env("PEXELS_API_KEY", default="")
    PIXABAY_API_KEY: str = get_env("PIXABAY_API_KEY", default="")

    # Logging / Runtime
    LOG_LEVEL: str = get_env("LOG_LEVEL", default="INFO")
    VIDEO_OUTPUT_DIR: str = get_env("VIDEO_OUTPUT_DIR", default="output")


config = Config()