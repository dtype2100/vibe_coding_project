import streamlit as st
import json
import os
import pickle
import numpy as np
from uuid import uuid4
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import faiss

# DB 파일 경로: 기존 업그레이드 버전도 지원
DB_FILE = (
    "vibe_prompts_structured.json"
    if os.path.exists("vibe_prompts_structured.json")
    else "vibe_prompts_structured_upgraded.json"
)

# 벡터 인덱스 파일 경로
VECTOR_INDEX_FILE = "prompt_vectors.faiss"
EMBEDDING_CACHE_FILE = "embeddings_cache.pkl"

# 임베딩 모델 초기화
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

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

# 프롬프트 텍스트를 임베딩으로 변환
def get_prompt_text(prompt: Dict) -> str:
    return f"{prompt.get('title', '')} {prompt.get('prompt', '')} {' '.join(prompt.get('keywords', []))}"

# 벡터 인덱스 생성 및 로드
@st.cache_data
def build_vector_index(prompts: List[Dict]):
    model = load_embedding_model()
    
    # 캐시된 임베딩이 있는지 확인
    if os.path.exists(EMBEDDING_CACHE_FILE):
        with open(EMBEDDING_CACHE_FILE, 'rb') as f:
            cached_data = pickle.load(f)
            if len(cached_data['prompts']) == len(prompts):
                return cached_data['index'], cached_data['embeddings']
    
    # 프롬프트 텍스트 생성
    prompt_texts = [get_prompt_text(prompt) for prompt in prompts]
    
    # 임베딩 생성
    embeddings = model.encode(prompt_texts, convert_to_numpy=True)
    
    # FAISS 인덱스 생성
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner Product (코사인 유사도)
    
    # 정규화 후 인덱스에 추가
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype('float32'))
    
    # 캐시 저장
    cache_data = {
        'index': index,
        'embeddings': embeddings,
        'prompts': prompts
    }
    with open(EMBEDDING_CACHE_FILE, 'wb') as f:
        pickle.dump(cache_data, f)
    
    return index, embeddings

# 벡터 기반 추천
def vector_recommend(user_input: str, prompts: List[Dict], top_k: int = 3) -> List[Dict]:
    if not prompts:
        return []
    
    model = load_embedding_model()
    index, embeddings = build_vector_index(prompts)
    
    # 사용자 입력을 임베딩으로 변환
    query_embedding = model.encode([user_input], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    
    # 유사도 검색
    scores, indices = index.search(query_embedding.astype('float32'), min(top_k, len(prompts)))
    
    # 결과 반환
    results = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx < len(prompts):
            prompt = prompts[idx].copy()
            prompt['similarity_score'] = float(score)
            results.append(prompt)
    
    return results

# 하이브리드 추천 (키워드 + 벡터)
def hybrid_recommend(user_input: str, prompts: List[Dict], top_k: int = 3) -> List[Dict]:
    # 키워드 기반 결과
    keyword_results = recommend(extract_tags(user_input), prompts, top_k * 2)
    
    # 벡터 기반 결과
    vector_results = vector_recommend(user_input, prompts, top_k * 2)
    
    # 결과 결합 및 중복 제거
    combined = {}
    
    # 키워드 결과 (가중치 0.4)
    for i, item in enumerate(keyword_results):
        item_id = item.get('id')
        score = (len(keyword_results) - i) * 0.4
        combined[item_id] = {'item': item, 'score': score}
    
    # 벡터 결과 (가중치 0.6)
    for i, item in enumerate(vector_results):
        item_id = item.get('id')
        vector_score = item.get('similarity_score', 0) * 0.6
        
        if item_id in combined:
            combined[item_id]['score'] += vector_score
        else:
            combined[item_id] = {'item': item, 'score': vector_score}
    
    # 점수 기준 정렬
    sorted_results = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
    
    return [result['item'] for result in sorted_results[:top_k]]

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
    recommend_mode = st.radio('추천 방식 선택', ['키워드 기반', '벡터 기반', '하이브리드'])
    user_input = st.text_input("원하는 작업을 설명해주세요", placeholder="예: fastapi로 로그인 api 만들고 싶어")

    if user_input:
        prompts = load_prompts()
        if recommend_mode == '키워드 기반':
            results = recommend(extract_tags(user_input), prompts)
        elif recommend_mode == '벡터 기반':
            results = vector_recommend(user_input, prompts)
        else:  # 하이브리드
            results = hybrid_recommend(user_input, prompts)

        if results:
            st.subheader("🔍 추천 프롬프트")
            for item in results:
                st.markdown(f"**{item.get('title')}**")
                st.code(item.get("prompt", ""), language="text")
                info_parts = [f"분야: `{item.get('category')}`", f"도구: `{item.get('tool')}`", f"레벨: `{item.get('level')}`"]
                if 'similarity_score' in item:
                    info_parts.append(f"유사도: `{item['similarity_score']:.3f}`")
                st.markdown(" / ".join(info_parts))
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
