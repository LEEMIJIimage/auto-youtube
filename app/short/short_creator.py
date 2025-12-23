import requests
import numpy as np
from io import BytesIO
import logging
from pathlib import Path
import re

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
    max_lines: int = 3,
    bg_alpha: int = 170,
) -> np.ndarray:
    """
    숏츠용: 하단 박스 자막(전체 화면 덮임 방지)
    """
    w, h = canvas_size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(w * 0.07)
    max_width = w - margin * 2

    def load_font(size: int):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                return ImageFont.load_default()
        return ImageFont.load_default()

    # 유튜브 숏츠 플레이어 컨트롤/하단 UI에 가려지는 걸 피하려고
    # 자막 박스를 바닥에 붙이지 않고 약간 위로 올린다.
    safe_bottom_ratio = float(getattr(settings, "SHORT_SUBTITLE_SAFE_BOTTOM_RATIO", 0.06))
    safe_bottom_margin = int(h * safe_bottom_ratio)
    box_height_ratio = float(getattr(settings, "SHORT_SUBTITLE_BOX_HEIGHT_RATIO", box_height_ratio))
    max_lines = int(getattr(settings, "SHORT_SUBTITLE_MAX_LINES", max_lines))

    box_h = int(h * box_height_ratio)
    box_bottom = h - safe_bottom_margin
    box_top = max(0, box_bottom - box_h)

    pad_y = 18
    pad_x = margin

    # 텍스트가 박스 안에 "절대" 안 잘리도록 폰트 사이즈 자동 축소
    # 우선 목표: 'ellipsis 없이' max_lines 안에 전체 문장을 넣기
    font = load_font(font_size)
    # 너무 일찍 폰트 축소를 멈추면 불필요하게 "…"이 생김.
    # 숏츠는 화면이 크므로 충분히 줄일 수 있게 하한을 낮춘다.
    min_font = 18
    fitted_lines: list[str] = []

    for _ in range(60):
        # 래핑(공백 없는 한글 포함)
        lines = wrap_text_by_width(draw, text or "", font, max_width)

        ascent, descent = font.getmetrics()
        line_h = ascent + descent + 12
        # max_lines 제한 내에서 전체 문장이 다 들어가는지 확인
        block_h = line_h * min(len(lines), max_lines if max_lines > 0 else len(lines))

        # 가로도 체크(혹시 폰트 로딩 실패 등으로 폭 계산이 이상할 때 대비)
        widest = 0.0
        for line in lines:
            widest = max(widest, draw.textlength(line, font=font))

        # ellipsis 없이 max_lines 내로 들어가는 경우
        if (len(lines) <= max_lines) and (block_h <= (box_h - pad_y * 2)) and (widest <= (max_width)):
            fitted_lines = lines
            break

        # 더 줄일 수 없으면 중단
        if font_size <= min_font:
            fitted_lines = lines
            break
        font_size -= 2
        font = load_font(font_size)

    # 아직도 라인이 많다면(=max_lines를 넘는다면) 이때만 ellipsis 처리
    lines = fitted_lines if fitted_lines else wrap_text_by_width(draw, text or "", font, max_width)
    if max_lines and len(lines) > max_lines:
        kept = lines[:max_lines]
        # 마지막 줄을 말줄임으로 마무리(단어 중간도 허용)
        last = kept[-1].rstrip()
        kept[-1] = (last[:-1] if len(last) > 1 else last) + "…"
        lines = kept

    bg = Image.new("RGBA", (w, box_h), (0, 0, 0, bg_alpha))
    img.paste(bg, (0, box_top))

    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 12
    block_h = line_h * len(lines)
    y = box_top + max(pad_y, (box_h - block_h) // 2)

    for line in lines:
        tw = draw.textlength(line, font=font)
        x = (w - tw) // 2
        for ox, oy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,3),(-3,3),(3,-3)]:
            draw.text((x+ox, y+oy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h

    return np.array(img)

def split_short_segments(text: str) -> list[str]:
    """
    숏츠 스크립트가 번호 목록 형태(1.~5.)로 오는 경우가 많아서
    각 라인을 '한 문구' 세그먼트로 분리한다.
    """
    if not text:
        return []
    segs: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        # "1. " 제거
        s = re.sub(r"^\d+\.\s*", "", s)
        # 감싼 따옴표 제거
        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "“" and s[-1] == "”")):
            s = s[1:-1].strip()
        if s:
            segs.append(s)
    return segs


def split_long_segment(seg: str, max_len: int = 45) -> list[str]:
    """
    한 세그먼트가 너무 길어서 박스/줄수 제한으로 '…'이 생기는 것을 방지하기 위해
    문장을 더 짧은 조각으로 분해한다.
    - 우선 구두점/쉼표 기준으로 나눈 뒤
    - 그래도 길면 max_len 기준으로 합치고
    - 최후에는 하드 컷
    """
    seg = (seg or "").strip()
    if not seg:
        return []
    if len(seg) <= max_len:
        return [seg]

    parts = [p.strip() for p in re.split(r"([,，]|[.!?]|…)+", seg) if p and p.strip()]
    if not parts:
        parts = [seg]

    out: list[str] = []
    cur = ""
    for p in parts:
        if not cur:
            cur = p
            continue
        # 다음 조각을 붙였을 때 너무 길면 flush
        if len(cur) + 1 + len(p) <= max_len:
            cur = f"{cur} {p}"
        else:
            out.append(cur)
            cur = p
    if cur:
        out.append(cur)

    # 여전히 긴 조각은 하드 컷
    final: list[str] = []
    for s in out:
        if len(s) <= max_len:
            final.append(s)
        else:
            for i in range(0, len(s), max_len):
                final.append(s[i : i + max_len].strip())
    return [x for x in final if x]


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

    # 자막도 세그먼트로 분리해서 시간에 따라 교체 (롱폼과 동일한 UX)
    segments = split_short_segments(text)
    if not segments:
        segments = [(text or "").strip()]
    segments = [s for s in segments if s]
    if not segments:
        segments = [""]

    # 너무 긴 세그먼트는 추가로 분해해서 "…" 발생을 최소화
    expanded: list[str] = []
    for s in segments:
        expanded.extend(split_long_segment(s, max_len=45))
    segments = expanded or segments

    seg_duration = duration / len(segments)
    logger.info("subtitle_segments=%s seg_duration=%.2fs", len(segments), seg_duration)

    subtitle_clips = []
    for i, seg in enumerate(segments):
        start = i * seg_duration
        subtitle_np = make_bottom_subtitle_image(
            text=seg,
            canvas_size=settings.SHORT_VIDEO_RESOLUTION,
            font_path=str(settings.FONT_PATH) if hasattr(settings, "FONT_PATH") else None,
            font_size=settings.SHORT_FONT_SIZE,
            max_lines=int(getattr(settings, "SHORT_SUBTITLE_MAX_LINES", 3)),
            box_height_ratio=float(getattr(settings, "SHORT_SUBTITLE_BOX_HEIGHT_RATIO", 0.32)),
        )
        subtitle_clips.append(ImageClip(subtitle_np).set_start(start).set_duration(seg_duration))

    final = CompositeVideoClip([slideshow, *subtitle_clips])
    final.write_videofile(
        output,
        fps=settings.VIDEO_FPS,
        codec="libx264",
        audio=False
    )

    return output