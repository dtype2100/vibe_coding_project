import streamlit as st
import json
import os
from uuid import uuid4
from typing import List, Dict

# DB 파일 경로: 기존 업그레이드 버전도 지원
DB_FILE = (
    "vibe_prompts_structured.json"
    if os.path.exists("vibe_prompts_structured.json")
    else "vibe_prompts_structured_upgraded.json"
)

# Load prompts
def load_prompts() -> List[Dict]:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save prompts
def save_prompts(prompts: List[Dict]) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

# Extract tags from user input
def extract_tags(text: str) -> Dict[str, List[str]]:
    text_lower = text.lower()
    category_keywords = {
        "프론트엔드": ["ui", "폼", "리액트", "react", "tailwind", "상태", "프론트"],
        "백엔드": ["api", "로그인", "fastapi", "서버", "rest", "인증"],
        "AI/LLM": ["gpt", "llm", "요약", "langchain", "llama", "프롬프트"],
        "데이터분석": ["pandas", "시각화", "csv", "plotly", "분석", "데이터"],
        "DevOps": ["docker", "배포", "ci", "github actions"],
        "기초": ["홀수", "짝수", "기초", "python", "입문"]
    }
    matched_categories = []
    matched_keywords = []
    for category, keywords in category_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                matched_categories.append(category)
                matched_keywords.append(kw)
    return {
        "categories": sorted(set(matched_categories)),
        "keywords": sorted(set(matched_keywords))
    }

# Simple keyword-based recommendation
def recommend(tags: Dict[str, List[str]], prompts: List[Dict], top_k: int = 3) -> List[Dict]:
    scored = []
    for prompt in prompts:
        score = 0
        if prompt.get("category") in tags["categories"]:
            score += 2
        score += len(set(tags["keywords"]) & set(prompt.get("keywords", [])))
        if score > 0:
            scored.append((score, prompt))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [item for _, item in scored[:top_k]]

# Placeholder for vector-based recommendation
def vector_recommend(user_input: str, prompts: List[Dict], top_k: int = 3) -> List[Dict]:
    # TODO: 임베딩+유사도 검색 구현 예정
    tags = extract_tags(user_input)
    return recommend(tags, prompts, top_k)

# Streamlit UI 설정
st.set_page_config(page_title="Vibe Coding Prompt Recommender", layout="wide")
st.title("🧠 바이브 코딩 프롬프트 추천 시스템")

tab1, tab2, tab3 = st.tabs(["✨ 추천 받기", "📄 프롬프트 목록", "➕ 프롬프트 추가"])

# Tab 1: 추천 받기
with tab1:
    st.markdown("💡 예시: `react 로그인 폼`, `fastapi 파일 업로드`, `llama-cpp 요약 챗봇`, `csv 시각화`")
    with st.expander("🧠 입력 가이드 보기"):
        st.markdown(
            """
        - **하고 싶은 작업을 간결하게 설명해주세요.**
        - 가능한 한 기술 이름이나 키워드를 포함하세요 (예: `fastapi`, `csv`, `jwt`, `react`, `llama` 등).
        - 예시 입력:
            - `fastapi로 로그인 기능 만들기`
            - `csv 파일을 업로드해서 plotly로 시각화`
            - `llama-cpp로 요약 챗봇 만들기`
        """
        )
    recommend_mode = st.radio('추천 방식 선택', ['키워드 기반', '벡터 기반'])
    user_input = st.text_input("원하는 작업을 설명해주세요", placeholder="예: fastapi로 로그인 api 만들고 싶어")

    if user_input:
        prompts = load_prompts()
        if recommend_mode == '키워드 기반':
            results = recommend(extract_tags(user_input), prompts)
        else:
            results = vector_recommend(user_input, prompts)

        if results:
            st.subheader("🔍 추천 프롬프트")
            for item in results:
                st.markdown(f"**{item.get('title')}**")
                st.code(item.get("prompt", ""), language="text")
                st.markdown(
                    f"분야: `{item.get('category')}` / 도구: `{item.get('tool')}` / 레벨: `{item.get('level')}`"
                )
                st.markdown("---")
        else:
            st.warning("적절한 프롬프트를 찾지 못했어요. 입력을 좀 더 구체화해보세요.")

# Tab 2: 프롬프트 목록
with tab2:
    st.subheader("📄 전체 프롬프트 목록")
    prompts = load_prompts()
    if prompts:
        for item in prompts:
            with st.expander(f"{item.get('title')} [{item.get('category')}]"):
                st.markdown(item.get("prompt", ""))
                st.markdown(
                    f"레벨: `{item.get('level')}` / 도구: `{item.get('tool')}` / 키워드: {', '.join(item.get('keywords', []))}"
                )
    else:
        st.info("저장된 프롬프트가 없습니다. ➕ '프롬프트 추가' 탭에서 새 프롬프트를 만들어보세요.")

# Tab 3: 프롬프트 추가
with tab3:
    st.subheader("➕ 새 프롬프트 추가")
    with st.form("add_form"):
        title = st.text_input("프롬프트 제목")
        prompt = st.text_area("프롬프트 내용")
        category = st.selectbox(
            "분야", ["프론트엔드", "백엔드", "AI/LLM", "데이터분석", "DevOps", "기초"]
        )
        tool = st.text_input("도구 이름 (예: React, FastAPI)")
        framework = st.text_input("프레임워크 이름 (예: Next.js, Streamlit)")
        level = st.selectbox("레벨", ["입문", "중급", "고급"])
        keywords = st.text_input("키워드 (쉼표로 구분)")
        submitted = st.form_submit_button("저장")
        if submitted:
            new_item = {
                "id": str(uuid4()),
                "title": title,
                "prompt": prompt,
                "category": category,
                "tool": tool,
                "framework": framework,
                "level": level,
                "keywords": [kw.strip() for kw in keywords.split(",") if kw.strip()]
            }
            prompts = load_prompts()
            prompts.append(new_item)
            save_prompts(prompts)
            st.success("프롬프트가 저장되었습니다.")
