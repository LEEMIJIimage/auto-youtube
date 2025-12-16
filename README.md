# Auto YouTube

웹 크롤링과 AI를 활용하여 자동으로 YouTube 영상을 업로드하는 프로젝트입니다.

## 프로젝트 구조

```
auto-youtube/
├── app/
│   ├── ai/                    # AI 제공자 모듈
│   ├── search/                # 검색 제공자 모듈
│   ├── generator/             # 스크립트 생성 모듈
│   ├── video/                 # 비디오 생성 모듈
│   ├── short/                 # 쇼츠 생성 모듈
│   ├── pipeline/              # 파이프라인 모듈
│   └── utils/                 # 유틸리티 모듈
├── assets/                    # 에셋 파일 (BGM 등)
├── config/                    # 설정 파일
├── main.py                    # 메인 진입점
└── requirements.txt           # 의존성 패키지
```

## 설치

1. 저장소 클론:
```bash
git clone <repository-url>
cd auto-youtube
```

2. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
```bash
cp config/env.example .env
# .env 파일을 편집하여 API 키를 입력하세요
```

## 사용법

```bash
python main.py --pipeline crime --topic "범죄 뉴스 주제"
```

## 설정

`config/settings.py` 파일에서 애플리케이션 설정을 관리할 수 있습니다.

`.env` 파일에 다음 API 키를 설정해야 합니다:
- `OPENAI_API_KEY`: OpenAI API 키
- `GROQ_API_KEY`: Groq API 키
- `BING_SEARCH_API_KEY`: Bing Search API 키

## 개발 상태

현재 프로젝트는 기본 구조만 구현되어 있으며, 각 모듈의 실제 기능 구현이 필요합니다.

## 라이선스

MIT License

