import requests
import numpy as np
from io import BytesIO
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip

from config import settings


def make_center_text_image(
    text: str,
    canvas_size: tuple[int, int],
    font_path: str | None,
    font_size: int,
    bg_alpha: int = 0
) -> np.ndarray:
    w, h = canvas_size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0 if bg_alpha == 0 else bg_alpha))
    draw = ImageDraw.Draw(img)

    # 폰트 로드 (한글이면 ttf 필수)
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # 간단 래핑
    max_width = int(w * 0.85)
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

    # 전체 높이 계산
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 12
    block_h = line_h * len(lines)

    y = (h - block_h) // 2
    for line in lines:
        tw = draw.textlength(line, font=font)
        x = (w - tw) // 2

        # outline
        for ox, oy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,3),(-3,3),(3,-3)]:
            draw.text((x+ox, y+oy), line, font=font, fill=(0, 0, 0, 255))
        # main
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

        y += line_h

    # RGBA로 반환해야 투명도 유지
    return np.array(img)

def wrap_text_by_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """
    공백이 거의 없는 한글도 깨지지 않게 '폭 기준'으로 래핑.
    - 공백 기준으로 먼저 시도
    - 한 단어(토큰)가 너무 길면 문자 단위로 하드 래핑
    """
    text = (text or "").strip()
    if not text:
        return []

    lines: list[str] = []
    for raw_line in text.split("\n"):
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        tokens = raw_line.split(" ")
        cur = ""

        def flush():
            nonlocal cur
            if cur:
                lines.append(cur)
                cur = ""

        for tok in tokens:
            if not tok:
                continue

            # 토큰 자체가 너무 길면(공백 없는 한글 등) 문자 단위로 자른다
            if draw.textlength(tok, font=font) > max_width:
                flush()
                buf = ""
                for ch in tok:
                    test = buf + ch
                    if draw.textlength(test, font=font) <= max_width:
                        buf = test
                    else:
                        if buf:
                            lines.append(buf)
                        buf = ch
                if buf:
                    lines.append(buf)
                continue

            test = (cur + " " + tok).strip() if cur else tok
            if draw.textlength(test, font=font) <= max_width:
                cur = test
            else:
                flush()
                cur = tok

        flush()

    return lines


def make_bottom_subtitle_image(
    text: str,
    canvas_size: tuple[int, int],
    font_path: str | None,
    font_size: int,
    box_height_ratio: float = 0.28,
    max_lines: int = 2,
    bg_alpha: int = 170,
) -> np.ndarray:
    """
    숏츠용: 하단 박스 자막(전체 화면 덮임 방지)
    """
    w, h = canvas_size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    margin = int(w * 0.07)
    max_width = w - margin * 2

    # 래핑(공백 없는 한글 포함)
    lines = wrap_text_by_width(draw, text or "", font, max_width)

    if max_lines and len(lines) > max_lines:
        kept = lines[:max_lines]
        kept[-1] = kept[-1][: max(0, len(kept[-1]) - 1)] + "…"
        lines = kept

    box_h = int(h * box_height_ratio)
    box_top = h - box_h
    bg = Image.new("RGBA", (w, box_h), (0, 0, 0, bg_alpha))
    img.paste(bg, (0, box_top))

    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 12
    block_h = line_h * len(lines)
    y = box_top + max(0, (box_h - block_h) // 2)

    for line in lines:
        tw = draw.textlength(line, font=font)
        x = (w - tw) // 2
        for ox, oy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,3),(-3,3),(3,-3)]:
            draw.text((x+ox, y+oy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h

    return np.array(img)


def create_short_video(text: str, image_url: str | list[str], output: str | None = None):
    logger = logging.getLogger("auto_youtube.video.short")
    if output is None:
        output = str(settings.SHORT_VIDEO_PATH)

    # image_url: str 또는 list[str] 허용 (여러 이미지 전환)
    sources = image_url if isinstance(image_url, list) else [image_url]
    sources = [s for s in sources if s]
    if not sources:
        sources = ["https://via.placeholder.com/1080x1920/111111/ffffff?text=No+Images"]

    duration = int(settings.SHORT_DURATION_SEC)
    slide = int(getattr(settings, "SHORT_IMAGE_DURATION_SEC", 2))
    if slide <= 0:
        slide = 2

    logger.info("start output=%s duration=%ss slide=%ss images=%s", output, duration, slide, len(sources))

    n = max(1, int(np.ceil(duration / slide)))
    cycle = [sources[i % len(sources)] for i in range(n)]

    clips = []
    for idx, src in enumerate(cycle):
        try:
            p = Path(str(src))
            if p.exists():
                img = Image.open(str(p)).convert("RGB")
            else:
                r = requests.get(src, timeout=15, headers={"User-Agent": "auto-youtube/1.0"})
                r.raise_for_status()
                img = Image.open(BytesIO(r.content)).convert("RGB")
            img = img.resize(settings.SHORT_VIDEO_RESOLUTION)
            clips.append(ImageClip(np.array(img)).set_duration(slide))
        except Exception as e:
            logger.exception("short_image_fail idx=%s src=%s err=%s", idx, src, e)

    if not clips:
        raise RuntimeError("No valid images for short video")

    from moviepy.editor import concatenate_videoclips
    slideshow = concatenate_videoclips(clips, method="compose").subclip(0, duration)

    # TextClip 대신 PIL 자막 이미지 (ImageMagick 불필요)
    subtitle_np = make_bottom_subtitle_image(
        text=text,
        canvas_size=settings.SHORT_VIDEO_RESOLUTION,
        font_path=str(settings.FONT_PATH) if hasattr(settings, "FONT_PATH") else None,
        font_size=settings.SHORT_FONT_SIZE,
        max_lines=2,
        box_height_ratio=0.28,
    )

    txt_clip = ImageClip(subtitle_np).set_duration(duration)

    final = CompositeVideoClip([slideshow, txt_clip])
    final.write_videofile(
        output,
        fps=settings.VIDEO_FPS,
        codec="libx264",
        audio=False
    )

    return output