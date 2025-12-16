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
    아래 내용을 기반으로 유튜브 5분짜리 '사건·사고·미스터리' 영상 스크립트를 작성해줘.

    조건:
    - 도입부는 강렬하게
    - 길이: 4000~6000자

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