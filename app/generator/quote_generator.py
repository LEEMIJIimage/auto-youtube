from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DailyQuotePayload:
    video_title: str
    quote_lines: list[str]
    typing_units: list[list[str]]
    tags: list[str]


def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _is_bad_punct_token(tok: str) -> bool:
    # "단독 구두점 토큰 금지" (예: "!", "..." 등)
    tok = (tok or "").strip()
    if not tok:
        return True
    # 한글/영문/숫자 중 하나라도 있으면 OK
    if re.search(r"[0-9A-Za-z가-힣]", tok):
        return False
    return True


def validate_daily_quote_payload(obj: dict[str, Any]) -> DailyQuotePayload:
    if not isinstance(obj, dict):
        raise ValueError("payload must be object")

    video_title = obj.get("video_title")
    quote_lines = obj.get("quote_lines")
    typing_units = obj.get("typing_units")
    tags = obj.get("tags")

    if not isinstance(video_title, str):
        raise ValueError("video_title must be string")
    video_title = video_title.strip()
    if not (6 <= len(video_title) <= 14):
        raise ValueError("video_title length must be 6~14")
    if ("하루 명언" not in video_title) and ("명언 모음" not in video_title):
        raise ValueError("video_title must include '하루 명언' or '명언 모음'")

    if not (isinstance(quote_lines, list) and all(isinstance(x, str) for x in quote_lines)):
        raise ValueError("quote_lines must be list[str]")
    if not (2 <= len(quote_lines) <= 4):
        raise ValueError("quote_lines length must be 2~4")

    cleaned_lines: list[str] = []
    for line in quote_lines:
        line = _collapse_spaces(line)
        if not (8 <= len(line) <= 18):
            raise ValueError("each quote_lines item must be 8~18 chars (including spaces)")
        cleaned_lines.append(line)

    if not (isinstance(typing_units, list) and all(isinstance(row, list) for row in typing_units)):
        raise ValueError("typing_units must be list[list[str]]")
    if len(typing_units) != len(cleaned_lines):
        raise ValueError("typing_units length must match quote_lines length")

    cleaned_units: list[list[str]] = []
    for i, row in enumerate(typing_units):
        if not all(isinstance(t, str) for t in row):
            raise ValueError("typing_units inner items must be string")
        if len(row) == 0:
            raise ValueError("typing_units row must not be empty")
        out_row: list[str] = []
        for tok in row:
            tok = tok.strip()
            if not (1 <= len(tok) <= 6):
                raise ValueError("token length must be 1~6")
            if _is_bad_punct_token(tok):
                raise ValueError("punct-only token not allowed")
            out_row.append(tok)
        # 단어 토큰은 공백으로 join 했을 때 quote_line과 일치해야 함(공백 normalize)
        rebuilt = _collapse_spaces(" ".join(out_row))
        if rebuilt != cleaned_lines[i]:
            raise ValueError("typing_units must tokenize quote_line by words")
        cleaned_units.append(out_row)

    if not (isinstance(tags, list) and all(isinstance(x, str) for x in tags)):
        raise ValueError("tags must be list[str]")
    tags = [t.strip().lstrip("#") for t in tags if t and t.strip()]
    if not (3 <= len(tags) <= 6):
        raise ValueError("tags length must be 3~6")
    # 해시태그용이니 너무 긴 건 컷
    tags = [t[:20] for t in tags]

    return DailyQuotePayload(
        video_title=video_title,
        quote_lines=cleaned_lines,
        typing_units=cleaned_units,
        tags=tags,
    )


def build_daily_quote_prompt(source_title: str, source_text: str) -> str:
    """
    OpenAI에 전달할 프롬프트(반드시 JSON만 반환).
    - "직접 인용 금지": 원문 문장을 그대로 복사하지 말라고 강하게 요구
    - quote_lines 길이/줄 수/토큰 규칙 명시
    """
    schema = {
        "video_title": "6~14자 한국어, 반드시 '하루 명언' 또는 '명언 모음' 포함",
        "quote_lines": ["8~18자(공백 포함) 한국어 문장", "2~4줄"],
        "typing_units": [["각 줄을 공백 기준 단어 토큰으로 분해(1~6자)"], "quote_lines와 동일한 줄 수"],
        "tags": ["3~6개, 해시태그용(앞의 # 없이)"],
    }

    return f"""
너는 '하루 명언(명언모음집)' 유튜브 숏츠용 문구를 만드는 작가다.
아래 원문(제목+본문)을 참고하되, **절대 원문 문장을 그대로 복사하거나 직접 인용하지 마라.**
의미만 재구성해서 완전히 새로운 문장으로 만들어라. (직접 인용 금지)

출력은 반드시 JSON 하나만 반환하라. 코드블록 금지. 설명 금지. 추가 텍스트 금지.

제약:
- quote_lines: 2~4줄
- 각 줄은 8~18자(공백 포함)
- typing_units: quote_lines를 공백 기준 '단어 토큰' 배열로 분해한 2차원 리스트
  - 토큰 길이 1~6자
  - 단독 구두점 토큰 금지(예: "!", "...", "," 같은 토큰 금지)
  - typing_units를 공백으로 join하면 quote_lines와 정확히 일치해야 함(공백 normalize 기준)
- video_title: 6~14자 한국어, 반드시 '하루 명언' 또는 '명언 모음' 포함
- tags: 3~6개 (해시태그용), 앞에 # 없이

스키마 참고(설명용, 출력에 포함 금지):
{json.dumps(schema, ensure_ascii=False)}

원문 제목:
{source_title}

원문 본문:
{source_text}
""".strip()


def generate_daily_quote_json(ai, source_title: str, source_text: str, max_retries: int = 2) -> DailyQuotePayload:
    """
    OpenAI JSON 생성 + 스키마 검증 + (최대 1~2회) 재시도.
    """
    prompt = build_daily_quote_prompt(source_title, source_text)
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            if hasattr(ai, "generate_json"):
                obj = ai.generate_json(prompt)
            else:
                raw = ai.generate_text(prompt)
                obj = json.loads(raw)
            return validate_daily_quote_payload(obj)
        except Exception as e:
            last_err = e
            # 다음 시도는 "왜 실패했는지"를 포함해 더 강하게 유도
            prompt = prompt + f"\n\n이전 출력은 검증에 실패했다. 오류: {repr(e)}\n위 제약을 만족하는 JSON만 다시 출력하라."

    raise RuntimeError(f"Failed to generate valid quote JSON: {last_err}")


