"""Streamlit app for Prompt Recommendation System"""

import streamlit as st
import logging
from services.prompt_service import PromptService
from services.recommendation_service import RecommendationService
from config import CATEGORIES, LEVELS, ITEMS_PER_PAGE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
@st.cache_resource
def get_services():
    prompt_service = PromptService()
    recommendation_service = RecommendationService()
    return prompt_service, recommendation_service


def display_prompt(prompt):
    """Display a single prompt card"""
    with st.container():
        st.markdown(f"### {prompt.get('title', '제목 없음')}")
        st.code(prompt.get('prompt', ''), language='text')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**분야:** {prompt.get('category', 'N/A')}")
        with col2:
            st.markdown(f"**도구:** {prompt.get('tool', 'N/A')}")
        with col3:
            st.markdown(f"**레벨:** {prompt.get('level', 'N/A')}")
        
        if prompt.get('keywords'):
            st.markdown(f"**키워드:** {', '.join(prompt['keywords'])}")
        
        if 'similarity_score' in prompt:
            st.markdown(f"**유사도:** {prompt['similarity_score']:.3f}")
        
        st.divider()


def main():
    st.set_page_config(
        page_title="프롬프트 추천기",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 프롬프트 추천기")
    st.markdown("AI 코딩을 위한 최적의 프롬프트를 찾아보세요!")
    
    # Get services
    prompt_service, recommendation_service = get_services()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🔍 프롬프트 검색", "📚 전체 목록", "➕ 새 프롬프트"])
    
    # Tab 1: Search and Recommendations
    with tab1:
        st.subheader("무엇을 만들고 싶으신가요?")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            user_input = st.text_input(
                "작업 설명",
                placeholder="예: fastapi로 로그인 API 만들기"
            )
        with col2:
            search_mode = st.selectbox(
                "검색 방식",
                ["하이브리드", "키워드", "벡터"]
            )
        
        if user_input:
            prompts = prompt_service.load_prompts()
            
            if search_mode == "키워드":
                results = recommendation_service.keyword_recommend(user_input, prompts)
            elif search_mode == "벡터":
                results = recommendation_service.vector_recommend(user_input, prompts)
            else:  # 하이브리드
                results = recommendation_service.hybrid_recommend(user_input, prompts)
            
            if results:
                st.subheader(f"추천 프롬프트 ({len(results)}개)")
                for prompt in results:
                    display_prompt(prompt)
            else:
                st.warning("관련 프롬프트를 찾을 수 없습니다. 다른 키워드로 검색해보세요.")
    
    # Tab 2: Browse All
    with tab2:
        st.subheader("전체 프롬프트 목록")
        
        prompts = prompt_service.load_prompts()
        
        if prompts:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_category = st.selectbox(
                    "분야 필터",
                    ["전체"] + CATEGORIES
                )
            with col2:
                selected_level = st.selectbox(
                    "레벨 필터",
                    ["전체"] + LEVELS
                )
            with col3:
                search_text = st.text_input("텍스트 검색")
            
            # Apply filters
            filtered = prompts
            if selected_category != "전체":
                filtered = [p for p in filtered if p.get("category") == selected_category]
            if selected_level != "전체":
                filtered = [p for p in filtered if p.get("level") == selected_level]
            if search_text:
                search_lower = search_text.lower()
                filtered = [p for p in filtered if 
                           search_lower in p.get("title", "").lower() or
                           search_lower in p.get("prompt", "").lower()]
            
            # Display
            st.markdown(f"**총 {len(filtered)}개의 프롬프트**")
            
            # Pagination
            if filtered:
                total_pages = (len(filtered) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
                page = st.number_input("페이지", min_value=1, max_value=total_pages, value=1)
                
                start_idx = (page - 1) * ITEMS_PER_PAGE
                end_idx = start_idx + ITEMS_PER_PAGE
                
                for prompt in filtered[start_idx:end_idx]:
                    display_prompt(prompt)
        else:
            st.info("아직 저장된 프롬프트가 없습니다.")
    
    # Tab 3: Add New
    with tab3:
        st.subheader("새 프롬프트 추가")
        
        with st.form("add_prompt_form"):
            title = st.text_input("제목", placeholder="예: FastAPI 로그인 API")
            prompt = st.text_area("프롬프트", placeholder="프롬프트 내용을 입력하세요")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                category = st.selectbox("분야", CATEGORIES)
            with col2:
                tool = st.text_input("도구", placeholder="예: FastAPI")
            with col3:
                level = st.selectbox("레벨", LEVELS)
            
            keywords = st.text_input("키워드 (쉼표로 구분)", placeholder="예: api, login, jwt")
            
            submitted = st.form_submit_button("저장하기")
            
            if submitted:
                if not title or not prompt:
                    st.error("제목과 프롬프트는 필수입니다.")
                else:
                    keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]
                    
                    result = prompt_service.add_prompt(
                        title=title,
                        prompt=prompt,
                        category=category,
                        tool=tool,
                        level=level,
                        keywords=keywords_list
                    )
                    
                    if result:
                        st.success("프롬프트가 저장되었습니다!")
                        st.cache_resource.clear()
                    else:
                        st.error("저장 중 오류가 발생했습니다.")


if __name__ == "__main__":
    main()