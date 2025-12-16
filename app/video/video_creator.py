import logging
import math
from pathlib import Path

from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import numpy as np
from config import settings

def create_long_video(script_text, image_urls, output_path=None):
    logger = logging.getLogger("auto_youtube.video.long")
    if output_path is None:
        output_path = str(settings.LONG_VIDEO_PATH)

    target_duration = int(getattr(settings, "LONG_DURATION_SEC", 300))
    image_duration = int(getattr(settings, "LONG_IMAGE_DURATION_SEC", 3))
    if image_duration <= 0:
        image_duration = 3

    logger.info(
        "start output=%s target_duration=%ss image_duration=%ss urls=%s",
        output_path,
        target_duration,
        image_duration,
        len(image_urls) if image_urls else 0,
    )

    if not image_urls:
        logger.warning("image_urls empty -> using placeholder")
        image_urls = ["https://via.placeholder.com/1920x1080/111111/ffffff?text=No+Images"]

    # 5분을 채우기 위해 이미지 URL을 순환(cycle)
    required_clips = max(1, math.ceil(target_duration / image_duration))
    logger.info("required_clips=%s (target/image_duration)", required_clips)

    url_cycle = [image_urls[i % len(image_urls)] for i in range(required_clips)]

    # URL별 다운로드 캐시(같은 URL 반복 다운로드 방지)
    cache: dict[str, np.ndarray] = {}
    clips = []
    ok = 0
    fail = 0
    headers = {"User-Agent": "auto-youtube/1.0"}

    for idx, url in enumerate(url_cycle):
        try:
            if url not in cache:
                logger.debug("load_image idx=%s src=%s", idx, url)
                # 로컬 파일이면 그대로 사용, 아니면 URL 다운로드
                p = Path(str(url))
                if p.exists():
                    img = Image.open(str(p)).convert("RGB")
                else:
                    r = requests.get(url, timeout=15, headers=headers)
                    r.raise_for_status()
                    img = Image.open(BytesIO(r.content)).convert("RGB")
                img = img.resize(settings.LONG_VIDEO_RESOLUTION)
                cache[url] = np.array(img)
            img_np = cache[url]
            clips.append(ImageClip(img_np).set_duration(image_duration))
            ok += 1
        except Exception as e:
            fail += 1
            logger.exception("image_fail idx=%s url=%s err=%s", idx, url, e)

    if not clips:
        raise RuntimeError("No valid images to build video (all downloads/decodes failed)")

    slideshow = concatenate_videoclips(clips, method="compose")
    logger.info("slideshow duration=%ss ok=%s fail=%s unique_images=%s", slideshow.duration, ok, fail, len(cache))

    # --------- 자막을 '전체 스크립트 1장'이 아닌, 구간별로 분할 ---------
    segments = split_text(script_text, max_chars=48)
    if not segments:
        segments = [""]

    seg_duration = slideshow.duration / len(segments)
    logger.info("subtitle_segments=%s seg_duration=%.2fs", len(segments), seg_duration)

    subtitle_clips = []
    for i, seg in enumerate(segments):
        start = i * seg_duration
        img_np = make_subtitle_image(
            text=seg,
            canvas_size=settings.LONG_VIDEO_RESOLUTION,
            font_path=str(settings.FONT_PATH) if hasattr(settings, "FONT_PATH") else None,
            font_size=settings.LONG_FONT_SIZE,
            max_lines=3,
            box_height_ratio=0.28,
        )
        subtitle_clips.append(
            ImageClip(img_np).set_start(start).set_duration(seg_duration)
        )

    if settings.BGM_PATH.exists():
        bgm = AudioFileClip(str(settings.BGM_PATH)).volumex(0.2)
        final = CompositeVideoClip([slideshow, *subtitle_clips])
        final.audio = bgm
    else:
        final = CompositeVideoClip([slideshow, *subtitle_clips])

    final.write_videofile(output_path, fps=settings.VIDEO_FPS)
    return output_path

def split_text(text: str, max_chars: int = 48) -> list[str]:
    """
    자막용 텍스트를 짧은 덩어리로 쪼갠다.
    - 한국어/영어 혼합에 대해 공백 기준 우선 분할, 너무 길면 하드 컷
    """
    text = (text or "").strip()
    if not text:
        return []

    # 줄바꿈은 강제 세그먼트 경계로 취급
    raw_parts = [p.strip() for p in text.split("\n") if p.strip()]
    parts: list[str] = []
    for part in raw_parts:
        if len(part) <= max_chars:
            parts.append(part)
            continue

        words = part.split(" ")
        cur = ""
        for w in words:
            if not cur:
                cur = w
                continue
            if len(cur) + 1 + len(w) <= max_chars:
                cur = f"{cur} {w}"
            else:
                parts.append(cur)
                cur = w
        if cur:
            parts.append(cur)

    # 공백이 거의 없는 경우(한국어 긴 문장) 하드 컷
    out: list[str] = []
    for p in parts:
        if len(p) <= max_chars:
            out.append(p)
        else:
            for i in range(0, len(p), max_chars):
                out.append(p[i:i+max_chars])
    return out

def make_subtitle_image(
    text: str,
    canvas_size: tuple[int, int],
    font_path: str | None,
    font_size: int,
    margin: int = 60,
    line_spacing: int = 10,
    bg_alpha: int = 160,
    max_lines: int = 3,
    box_height_ratio: float = 0.28,
) -> np.ndarray:
    """
    ImageMagick 없이 자막을 이미지로 만든다.
    - canvas_size: (width, height)
    - font_path: ttf 경로 (없으면 기본 폰트)
    - bg_alpha: 자막 배경 반투명(0~255)
    """
    w, h = canvas_size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 폰트 로드
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # 간단한 줄바꿈 래핑(너무 길면 여러 줄)
    # 대략적인 글자 폭 기준으로 나눔 (정교하게 하려면 measure 기반으로 개선 가능)
    max_width = w - margin * 2

    lines = []
    for raw_line in text.split("\n"):
        words = raw_line.split(" ")
        cur = ""
        for word in words:
            test = (cur + " " + word).strip()
            tw = draw.textlength(test, font=font)
            if tw <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)

    # 하단 고정 박스 안에만 자막을 그린다 (전체 화면 덮임 방지)
    box_h = int(h * box_height_ratio)
    box_top = h - box_h
    bg = Image.new("RGBA", (w, box_h), (0, 0, 0, bg_alpha))
    img.paste(bg, (0, box_top))

    # 라인 수 제한 + 말줄임
    if max_lines and len(lines) > max_lines:
        kept = lines[:max_lines]
        kept[-1] = kept[-1][: max(0, len(kept[-1]) - 1)] + "…"
        lines = kept

    ascent, descent = font.getmetrics()
    line_height = ascent + descent + line_spacing
    text_block_h = line_height * len(lines)

    x = margin
    y = box_top + max(0, (box_h - text_block_h) // 2)

    # 글자 그리기(흰색 + 검은색 외곽선 느낌을 간단히 구현)
    for i, line in enumerate(lines):
        yy = y + i * line_height

        # outline
        for ox, oy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2),(-2,2),(2,-2)]:
            draw.text((x+ox, yy+oy), line, font=font, fill=(0,0,0,255))
        # main
        draw.text((x, yy), line, font=font, fill=(255,255,255,255))

    # RGBA로 반환해야 투명도가 유지되어 이미지가 검게 덮이지 않는다.
    return np.array(img)