# 프롬프트 추천기

AI 코딩을 위한 최적의 프롬프트를 검색하고 추천받을 수 있는 시스템입니다.

## 주요 기능

1. **프롬프트 검색**
   - 키워드 기반 검색
   - 벡터 유사도 검색
   - 하이브리드 검색 (키워드 + 벡터)

2. **프롬프트 관리**
   - 전체 프롬프트 목록 보기
   - 분야/레벨별 필터링
   - 새 프롬프트 추가

3. **Supabase 연동**
   - 클라우드 데이터베이스 지원
   - 로컬 JSON 파일 폴백

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일에 Supabase 정보 입력
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

3. Supabase 테이블 생성:
```sql
CREATE TABLE prompts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    category TEXT,
    tool TEXT,
    level TEXT,
    keywords TEXT[]
);
```

## 실행 방법

```bash
streamlit run app.py
```

## 프로젝트 구조

```
prompt_recommendation/
├── app.py              # 메인 Streamlit 앱
├── config.py           # 설정 파일
├── services/
│   ├── prompt_service.py       # 프롬프트 CRUD
│   └── recommendation_service.py # 추천 로직
├── data/               # 로컬 데이터 (폴백용)
├── requirements.txt    # 패키지 목록
└── .env.example       # 환경변수 예시
```