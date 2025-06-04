import streamlit as st
import json
import os
from uuid import uuid4
from typing import List, Dict, Tuple

# Vector 기반 추천: HuggingFace Embeddings 사용
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# DB 파일 경로: 기존 업그레이드 버전도 지원
DB_FILE = (
    "vibe_prompts_structured.json"
    if os.path.exists("vibe_prompts_structured.json")
    else "vibe_prompts_structured_upgraded.json"
)

# Global constant for category keywords
CATEGORY_KEYWORDS_DATA = {
    "프론트엔드": ["ui", "폼", "리액트", "react", "tailwind", "상태", "프론트"],
    "백엔드": ["api", "로그인", "fastapi", "서버", "rest", "인증"],
    "AI/LLM": ["gpt", "llm", "요약", "langchain", "llama", "프롬프트"],
    "데이터분석": ["pandas", "시각화", "csv", "plotly", "분석", "데이터"],
    "DevOps": ["docker", "배포", "ci", "github actions"],
    "기초": ["홀수", "짝수", "기초", "python", "입문"]
}

# Load prompts
@st.cache_data
def load_prompts() -> List[Dict]:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.info("DB 파일이 존재하지 않아 새로 생성합니다. 프롬프트를 추가해보세요.")
        return []

# Save prompts
def save_prompts(prompts: List[Dict]) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

# Extract tags from user input
def extract_tags(text: str) -> Dict[str, List[str]]:
    text_lower = text.lower()
    matched_categories = []
    matched_keywords = []
    for category, keywords in CATEGORY_KEYWORDS_DATA.items(): # Use global constant
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
    scored: List[Tuple[int, Dict]] = []
    for prompt in prompts:
        score = 0
        if prompt.get("category") in tags["categories"]:
            score += 2
        score += len(set(tags["keywords"]) & set(prompt.get("keywords", [])))
        if score > 0:
            scored.append((score, prompt))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [item for _, item in scored[:top_k]]

# ---------------- Vector 기반 추천: HuggingFace Embeddings 사용 ----------------

@st.cache_resource
def build_vectorstore(prompts: List[Dict]) -> FAISS:
    # 한국어 특화 모델 사용
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    texts = [item.get("prompt", "") for item in prompts]
    vs = FAISS.from_texts(texts, embeddings, metadatas=prompts)
    return vs

# 입력 문장에 대해 벡터 유사도 검색 수행
def vector_recommend(user_input: str, vs: FAISS, top_k: int = 3) -> List[Dict]:
    if vs is None: # Handle case where vector_store might be None (e.g. no prompts)
        return []
    results = vs.similarity_search_with_score(user_input, k=top_k)
    return [doc.metadata for doc, _ in results]
# -----------------------------------------------------

# Streamlit UI 설정
st.set_page_config(
    page_title="Vibe Coding Prompt Recommender",
    layout="wide",
    initial_sidebar_state="expanded"
)
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

    prompts = load_prompts() # Load prompts once for the tab
    vector_store = None # Initialize vector_store
    if prompts: # Check if there are any prompts
        vector_store = build_vectorstore(prompts) 
    
    if user_input:
        if recommend_mode == '키워드 기반':
            results = recommend(extract_tags(user_input), prompts)
        else:
            if vector_store:
                results = vector_recommend(user_input, vector_store)
            else:
                results = [] # No vector store to search

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
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_category = st.multiselect(
                "분야 필터",
                options=sorted(set(p.get("category") for p in prompts)),
                default=[]
            )
        with col2:
            selected_level = st.multiselect(
                "레벨 필터",
                options=sorted(set(p.get("level") for p in prompts)),
                default=[]
            )
        with col3:
            selected_tool = st.multiselect(
                "도구 필터",
                options=sorted(set(p.get("tool") for p in prompts)),
                default=[]
            )
        
        # 검색 기능
        search_query = st.text_input("🔍 프롬프트 검색", placeholder="제목, 내용, 키워드로 검색")
        
        # 정렬 옵션
        sort_by = st.selectbox(
            "정렬 기준",
            ["최신순", "제목순", "분야순", "레벨순"]
        )
        
        # 필터링 및 검색 적용
        filtered_prompts = prompts
        if selected_category:
            filtered_prompts = [p for p in filtered_prompts if p.get("category") in selected_category]
        if selected_level:
            filtered_prompts = [p for p in filtered_prompts if p.get("level") in selected_level]
        if selected_tool:
            filtered_prompts = [p for p in filtered_prompts if p.get("tool") in selected_tool]
        if search_query:
            search_query = search_query.lower()
            filtered_prompts = [
                p for p in filtered_prompts
                if search_query in p.get("title", "").lower()
                or search_query in p.get("prompt", "").lower()
                or any(search_query in kw.lower() for kw in p.get("keywords", []))
            ]
        
        # 정렬 적용
        if sort_by == "최신순":
            filtered_prompts = filtered_prompts[::-1]  # 최신 추가된 순
        elif sort_by == "제목순":
            filtered_prompts = sorted(filtered_prompts, key=lambda x: x.get("title", ""))
        elif sort_by == "분야순":
            filtered_prompts = sorted(filtered_prompts, key=lambda x: (x.get("category", ""), x.get("title", "")))
        elif sort_by == "레벨순":
            level_order = {"입문": 0, "중급": 1, "고급": 2}
            filtered_prompts = sorted(filtered_prompts, key=lambda x: (level_order.get(x.get("level", ""), 0), x.get("title", "")))

        # 필터링 후 결과 확인
        if not filtered_prompts and prompts: # prompts가 비어있지 않은데 필터링 결과가 없는 경우
            st.warning("선택한 조건에 맞는 프롬프트가 없습니다.")
        
        st.markdown(f"**총 {len(filtered_prompts)}개의 프롬프트**")

        if filtered_prompts: # 필터링된 결과가 있을 때만 페이지네이션 및 목록 표시
            # 페이지네이션
            items_per_page = 10
            total_pages = (len(filtered_prompts) + items_per_page - 1) // items_per_page
            
            current_page = 1
            if total_pages > 1:
                current_page = st.selectbox(
                    "페이지",
                    range(1, total_pages + 1),
                    format_func=lambda x: f"페이지 {x} / {total_pages}"
                )
            
            # 현재 페이지의 프롬프트만 표시
            start_idx = (current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            current_prompts = filtered_prompts[start_idx:end_idx]
            
            for item in current_prompts:
            with st.expander(f"### {item.get('title')}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown("**프롬프트 내용**")
                    st.code(item.get("prompt", ""), language="text")
                with col2:
                    st.markdown("**메타데이터**")
                    st.markdown(f"📌 분야: `{item.get('category')}`")
                    st.markdown(f"🛠️ 도구: `{item.get('tool')}`")
                    st.markdown(f"📚 프레임워크: `{item.get('framework')}`")
                    st.markdown(f"⭐ 레벨: `{item.get('level')}`")
                    st.markdown("🔑 키워드:")
                    for kw in item.get("keywords", []):
                        st.markdown(f"- `{kw}`")
            st.markdown("---")
    else: # prompts 자체가 비어있는 경우
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
