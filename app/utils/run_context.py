from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging


@dataclass(frozen=True)
class RunContext:
    run_dir: Path
    images_dir: Path
    scripts_dir: Path


def create_run_context(output_root: Path) -> RunContext:
    """
    output_root 아래에 날짜_i 폴더를 만들고(예: 2025-12-12_1),
    실행 중 생성되는 아티팩트(이미지/스크립트)를 거기에 저장한다.
    """
    logger = logging.getLogger("auto_youtube.run")
    output_root.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d")
    pattern = re.compile(rf"^{re.escape(date)}_(\d+)$")

    max_i = 0
    for p in output_root.iterdir():
        if not p.is_dir():
            continue
        m = pattern.match(p.name)
        if m:
            try:
                max_i = max(max_i, int(m.group(1)))
            except ValueError:
                pass

    run_dir = output_root / f"{date}_{max_i + 1}"
    images_dir = run_dir / "images"
    scripts_dir = run_dir / "scripts"

    images_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)

    logger.info("run_dir=%s", run_dir)
    return RunContext(run_dir=run_dir, images_dir=images_dir, scripts_dir=scripts_dir)


