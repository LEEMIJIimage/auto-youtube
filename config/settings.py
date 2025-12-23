# config/settings.py

from pathlib import Path
from app.utils.config_loader import config

BASE_DIR = Path(__file__).resolve().parent.parent  # auto-youtube/

# ======================
# AI Policy
# ======================
AI_MODEL = "gpt-4o-mini"
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 1200

# ======================
# Pipeline Policy
# ======================
DEFAULT_NEWS_QUERY = "사건"
DEFAULT_NEWS_LIMIT = 1

# 콘텐츠(스크립트 재료) 소스 provider 우선순위 (fallback)
# 확장 예: ["reddit", "rss_google", "rss_bbc", "rss_naver"]
CONTENT_PROVIDER_PRIORITY = ["rss_google"]

# ======================
# Humor Pipeline Policy
# ======================
# Reddit 검색어(영문 권장) - 예: "funny", "joke", "tifu"
HUMOR_QUERY = "funny"
HUMOR_REDDIT_SUBREDDITS = ["funny", "tifu", "Jokes"]

# ======================
# Image Search Policy
# ======================
# 무료 이미지 provider 우선순위 (fallback)
IMAGE_PROVIDER_PRIORITY = ["unsplash", "pexels", "pixabay"]

# "유니크 이미지"를 몇 장 찾아올지 (롱폼은 여기서 가져온 이미지를 영상 길이(5분)에 맞춰 반복 재사용)
LONG_IMAGE_COUNT = 12
SHORT_IMAGE_COUNT = 3

# 숏츠에서 이미지 전환 주기(초)
SHORT_IMAGE_DURATION_SEC = 2

# 숏츠 자막 박스/줄수 정책
SHORT_SUBTITLE_MAX_LINES = 3
SHORT_SUBTITLE_BOX_HEIGHT_RATIO = 0.32
SHORT_SUBTITLE_SAFE_BOTTOM_RATIO = 0.08

# ======================
# Output Policy
# ======================
OUTPUT_DIR = BASE_DIR / config.VIDEO_OUTPUT_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LONG_VIDEO_FILENAME = "long_video.mp4"
SHORT_VIDEO_FILENAME = "short_video.mp4"

LONG_VIDEO_PATH = OUTPUT_DIR / LONG_VIDEO_FILENAME
SHORT_VIDEO_PATH = OUTPUT_DIR / SHORT_VIDEO_FILENAME

# ======================
# Video Policy
# ======================
LONG_VIDEO_RESOLUTION = (1920, 1080)   # 롱폼 기본 16:9
SHORT_VIDEO_RESOLUTION = (1080, 1920)  # 숏츠 9:16

VIDEO_FPS = 30
LONG_IMAGE_DURATION_SEC = 3      # 슬라이드 한 장당 3초
SHORT_DURATION_SEC = 10          # 숏츠 기본 길이

# 롱폼 목표 길이(초). 5분 = 300초
LONG_DURATION_SEC = 100

BGM_PATH = BASE_DIR / "assets" / "bgm" / "Nebula - The Grey Room _ Density & Time.mp3"
FONT_PATH = BASE_DIR / "assets" / "font" / "NanumGothic.ttf"

# Text (기본값만)
LONG_FONT_SIZE = 42
SHORT_FONT_SIZE = 70

# ======================
# Logging Policy
# ======================
LOG_LEVEL = config.LOG_LEVEL