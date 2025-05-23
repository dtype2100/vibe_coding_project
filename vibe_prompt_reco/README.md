# 🧠 Vibe Coding Prompt Recommender

## 📝 프로젝트 소개
Vibe Coding Prompt Recommender는 개발자들이 코딩 작업을 수행할 때 필요한 프롬프트를 추천해주는 웹 애플리케이션입니다. Streamlit을 기반으로 만들어졌으며, 사용자의 입력을 분석하여 관련된 코딩 프롬프트를 추천합니다. 이 프로젝트는 개발자들이 더 효율적으로 코딩할 수 있도록 도와주는 것이 목표입니다.

## ✨ 주요 기능
- **스마트 프롬프트 추천**: 사용자의 입력을 분석하여 최적화된 코딩 프롬프트를 추천
- **프롬프트 관리 시스템**: 새로운 프롬프트 추가 및 기존 프롬프트 조회
- **자동 카테고리 분류**: 프론트엔드, 백엔드, AI/LLM, 데이터분석, DevOps, 기초 등 다양한 카테고리 지원
- **키워드 기반 매칭**: 입력된 문장에서 자동으로 관련 키워드와 카테고리를 추출

## 🛠️ 기술 스택
- **Frontend**: Streamlit
- **Backend**: Python
- **Data Storage**: JSON
- **AI Integration**: 프롬프트 최적화 시스템

## 🚀 시작하기

### 필수 요구사항
- Python 3.7 이상
- Streamlit

### 설치 방법
1. 저장소 클론
```bash
git clone [repository-url]
cd vibe_prompt_reco
```

2. 필요한 패키지 설치
```bash
pip install streamlit
```

3. 애플리케이션 실행
```bash
streamlit run vibe_prompt_manager_app_commented.py
```

## 💡 사용 방법

### 1. 프롬프트 추천 받기
- 원하는 작업을 간단히 설명해주세요
- 기술 스택이나 키워드를 포함하면 더 정확한 추천을 받을 수 있습니다
- 예시:
  - "React로 로그인 폼 만들기"
  - "FastAPI로 파일 업로드 API 구현하기"
  - "Pandas로 CSV 데이터 분석하기"

### 2. 프롬프트 추가하기
- 제목: 프롬프트의 목적을 명확히 설명
- 내용: 구체적인 프롬프트 내용
- 카테고리: 프롬프트의 분야 선택
- 도구: 사용할 주요 기술/도구
- 프레임워크: 사용할 프레임워크
- 레벨: 난이도 설정 (입문/중급/고급)
- 키워드: 쉼표로 구분된 관련 키워드

## 📊 지원하는 카테고리와 키워드
- **프론트엔드**: UI, 폼, React, Tailwind, 상태관리, 컴포넌트 등
- **백엔드**: API, 로그인, FastAPI, 서버, REST, 인증, JWT 등
- **AI/LLM**: 요약, LangChain, Llama, 프롬프트 엔지니어링 등
- **데이터분석**: Pandas, 시각화, CSV, Plotly, 데이터 처리 등
- **DevOps**: Docker, 배포, CI, GitHub Actions, 컨테이너화 등
- **기초**: Python 기초, 입문자용 예제, 기본 문법 등

## 🔍 프롬프트 추천 알고리즘
1. 사용자 입력에서 키워드와 카테고리 추출
2. 카테고리 매칭 (2점)
3. 키워드 매칭 (1점/키워드)
4. 점수 기반 상위 3개 프롬프트 추천


