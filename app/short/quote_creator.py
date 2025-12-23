from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips

from config import settings


def _load_font(path: str | None, size: int):
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()
    return ImageFont.load_default()


def _render_frame(
    *,
    title: str,
    lines: list[str],
    resolution: tuple[int, int],
    title_font: ImageFont.ImageFont,
    body_font: ImageFont.ImageFont,
) -> np.ndarray:
    w, h = resolution
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # title (top)
    pad_x = int(w * 0.06)
    top_y = int(h * 0.06)
    draw.text((pad_x, top_y), title, font=title_font, fill=(255, 255, 255))

    # body (center)
    safe_top = int(h * 0.18)
    safe_bottom = int(h * 0.18)
    max_width = int(w * 0.88)

    # line heights
    ascent, descent = body_font.getmetrics()
    line_h = ascent + descent + 20
    block_h = line_h * len(lines)
    y = safe_top + max(0, ((h - safe_top - safe_bottom) - block_h) // 2)

    for line in lines:
        # 가운데 정렬
        tw = draw.textlength(line, font=body_font)
        x = (w - tw) // 2

        # outline
        for ox, oy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,3),(-3,3),(3,-3)]:
            draw.text((x+ox, y+oy), line, font=body_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=body_font, fill=(255, 255, 255))
        y += line_h

    return np.array(img)


def create_quote_short(
    *,
    video_title: str,
    quote_lines: list[str],
    typing_units: list[list[str]],
    output_path: str,
    token_interval_sec: float,
    hold_sec: float,
) -> str:
    logger = logging.getLogger("auto_youtube.quote_video")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = settings.SHORT_VIDEO_RESOLUTION
    duration = float(settings.SHORT_DURATION_SEC)

    # 토큰 총 개수
    total_tokens = sum(len(row) for row in typing_units)
    total_tokens = max(1, total_tokens)

    # duration 안에 들어오도록 interval 조정
    token_interval_sec = float(token_interval_sec)
    hold_sec = float(hold_sec)
    if hold_sec < 1.0:
        hold_sec = 1.0
    if hold_sec > duration * 0.4:
        hold_sec = duration * 0.4

    available = max(0.5, duration - hold_sec)
    max_interval = available / total_tokens
    interval = min(token_interval_sec, max_interval)
    # 너무 빠르게도 안 되게 (기본 바닥값)
    interval = max(0.06, interval)

    logger.info(
        "render start out=%s duration=%.2fs tokens=%s interval=%.3fs hold=%.2fs",
        out,
        duration,
        total_tokens,
        interval,
        hold_sec,
    )

    font_path = str(settings.FONT_PATH) if hasattr(settings, "FONT_PATH") else None
    title_font = _load_font(font_path, 44)
    body_font = _load_font(font_path, 86)

    # 타이핑 진행 상태
    current: list[list[str]] = [[] for _ in typing_units]
    clips: list[ImageClip] = []

    def make_display_lines() -> list[str]:
        lines = []
        for i in range(len(typing_units)):
            lines.append(" ".join(current[i]).strip())
        # 빈 줄도 표시되긴 해서, 최소한 공백 유지
        return [ln if ln else "" for ln in lines]

    # 토큰이 1개씩 추가되는 단계별 프레임 생성
    for i, row in enumerate(typing_units):
        for tok in row:
            current[i].append(tok)
            frame = _render_frame(
                title=video_title,
                lines=make_display_lines(),
                resolution=(w, h),
                title_font=title_font,
                body_font=body_font,
            )
            clips.append(ImageClip(frame).set_duration(interval))

    # 마지막 hold
    final_frame = _render_frame(
        title=video_title,
        lines=[" ".join(row).strip() for row in typing_units],
        resolution=(w, h),
        title_font=title_font,
        body_font=body_font,
    )
    clips.append(ImageClip(final_frame).set_duration(hold_sec))

    video = concatenate_videoclips(clips, method="compose").subclip(0, duration)
    video.write_videofile(
        str(out),
        fps=settings.VIDEO_FPS,
        codec="libx264",
        audio=False,
    )
    return str(out)


