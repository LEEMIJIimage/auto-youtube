def clean_stage_directions(text: str) -> str:
    """
    자막/영상용으로 '연출 지시문'을 제거한다.
    - RAW 스크립트는 그대로 저장하고,
    - 화면에 보여줄 때만 [인트로], (강렬한 음악과 함께...) 같은 구간을 제거.
    """
    import re

    if not text:
        return ""

    keywords = ("인트로", "아웃트로", "음악", "bgm", "효과음", "자막", "화면", "컷", "전환")

    def strip_brackets(s: str) -> str:
        # **[... ]** / [...] 제거 (키워드 포함 시)
        def repl(m):
            inner = m.group(1)
            if any(k in inner.lower() for k in keywords):
                return ""
            return m.group(0)

        s = re.sub(r"\*\*\[([^\]]+)\]\*\*", lambda m: repl(m), s)
        s = re.sub(r"\[([^\]]+)\]", lambda m: repl(m), s)

        # (...) 제거 (키워드 포함 시)
        def repl_p(m):
            inner = m.group(1)
            if any(k in inner.lower() for k in keywords):
                return ""
            return m.group(0)

        s = re.sub(r"\(([^\)]+)\)", lambda m: repl_p(m), s)
        return s

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cleaned = strip_brackets(stripped).strip()
        if cleaned:
            lines.append(cleaned)

    # 공백 정리
    out = "\n".join(lines)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out.strip()

def generate_long_script(ai, title, summary):
    prompt = f"""
    아래 내용을 기반으로 유튜브 5분짜리 영상 스크립트를 작성해줘.

    조건:
    - 길이: 4000~6000자
    - 선동가라면 이 내용을 어떻게 전달했을지를 염두에 두고.

    제목: {title}
    요약: {summary}
    """

    return ai.generate_text(prompt)


def generate_short_script(ai, long_script):
    prompt = f"""
    아래 스크립트에서 유튜브 숏츠용 5~15초 강렬한 문구를 만들어줘.

    스크립트:
    {long_script}
    """

    return ai.generate_text(prompt)


def generate_humor_long_script(ai, title: str, summary: str) -> str:
    """
    Reddit 유머/썰 기반으로 한국어 유튜브 롱폼(약 5분) 스크립트 생성.
    """
    prompt = f"""
    아래 내용을 기반으로 한국어 유튜브 '유머/썰' 롱폼 스크립트를 작성해줘.

    목적:
    - 시청자가 웃고 끝까지 보게 만드는 이야기 전개
    - 과장된 욕설/혐오/차별 표현 금지
    - 실존 인물/집단에 대한 공격 금지
    - 너무 노골적인 성적 내용 금지

    형식:
    - 오프닝(강한 훅) → 상황 설명 → 전개(포인트 2~3개) → 반전/결말 → 한 줄 마무리
    - 말하듯 자연스럽고 리듬감 있게
    - 길이: 3500~5500자

    원문 제목: {title}
    원문 요약/본문: {summary}
    """
    return ai.generate_text(prompt)


def generate_humor_short_script(ai, long_script: str) -> str:
    """
    롱폼에서 숏츠용 하이라이트 문구 여러 개(번호 리스트) 생성.
    """
    prompt = f"""
    아래 스크립트에서 유튜브 숏츠용 훅 문구를 5개 만들어줘.
    조건:
    - 각 문구는 1~2문장
    - 번호 리스트(1.~5.)로 출력
    - 과한 욕설/혐오/차별 표현 금지

    스크립트:
    {long_script}
    """
    return ai.generate_text(prompt)