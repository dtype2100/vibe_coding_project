"""
Main Streamlit application for Vibe Prompt Recommendation System
"""

import streamlit as st
import logging
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.prompt_service import PromptService
from services.recommendation_service import RecommendationService
from utils.config import (
    CATEGORIES, LEVELS, TOOLS, ITEMS_PER_PAGE,
    DB_FILE, EMBEDDING_CACHE_FILE, LOG_LEVEL, LOG_FORMAT
)
from utils.helpers import display_prompt_card, display_prompt_detail, validate_prompt_input

# Configure logging``
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services"""
    cache_path = EMBEDDING_CACHE_FILE
    prompt_service = PromptService()
    recommendation_service = RecommendationService(cache_file=cache_path)
    return prompt_service, recommendation_service

def main():
    """Main application function"""
    
    # Streamlit UI 설정
    st.set_page_config(
        page_title="Vibe Coding Prompt Recommender",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("🧠 바이브 코딩 프롬프트 추천 시스템")
    
    # Initialize services
    prompt_service, recommendation_service = get_services()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["✨ 추천 받기", "📄 프롬프트 목록", "➕ 프롬프트 추가"])
    
    # Tab 1: 추천 받기
    with tab1:
        show_recommendation_tab(recommendation_service, prompt_service)
    
    # Tab 2: 프롬프트 목록
    with tab2:
        show_browse_tab(prompt_service)
    
    # Tab 3: 프롬프트 추가
    with tab3:
        show_add_prompt_tab(prompt_service, recommendation_service)

def show_recommendation_tab(recommendation_service: RecommendationService, prompt_service: PromptService):
    """Show recommendation tab"""
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
        prompts = prompt_service.load_prompts()
        
        try:
            if recommend_mode == '키워드 기반':
                tags = recommendation_service.extract_tags(user_input)
                results = recommendation_service.keyword_recommend(tags, prompts)
            elif recommend_mode == '벡터 기반':
                results = recommendation_service.vector_recommend(user_input, prompts)
            else:  # 하이브리드
                results = recommendation_service.hybrid_recommend(user_input, prompts)
            
            if results:
                st.subheader("🔍 추천 프롬프트")
                for item in results:
                    display_prompt_card(item)
            else:
                st.warning("적절한 프롬프트를 찾지 못했어요. 입력을 좀 더 구체화해보세요.")
        
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            st.error("추천 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

def show_browse_tab(prompt_service: PromptService):
    """Show browse/list tab"""
    st.subheader("📄 전체 프롬프트 목록")
    prompts = prompt_service.load_prompts()
    
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
        
        # 필터링 및 정렬 적용
        from utils.helpers import filter_prompts, sort_prompts
        
        filtered_prompts = filter_prompts(
            prompts,
            categories=selected_category,
            levels=selected_level,
            tools=selected_tool,
            search_query=search_query
        )
        
        filtered_prompts = sort_prompts(filtered_prompts, sort_by)
        
        # 필터링 후 결과 확인
        if not filtered_prompts and prompts:
            st.warning("선택한 조건에 맞는 프롬프트가 없습니다.")
        
        st.markdown(f"**총 {len(filtered_prompts)}개의 프롬프트**")
        
        if filtered_prompts:
            # 페이지네이션
            total_pages = (len(filtered_prompts) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            
            current_page = 1
            if total_pages > 1:
                current_page = st.selectbox(
                    "페이지",
                    range(1, total_pages + 1),
                    format_func=lambda x: f"페이지 {x} / {total_pages}"
                )
            
            # 현재 페이지의 프롬프트만 표시
            start_idx = (current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            current_prompts = filtered_prompts[start_idx:end_idx]
            
            for item in current_prompts:
                display_prompt_detail(item)
    else:
        st.info("저장된 프롬프트가 없습니다. ➕ '프롬프트 추가' 탭에서 새 프롬프트를 만들어보세요.")

def show_add_prompt_tab(prompt_service: PromptService, recommendation_service: RecommendationService):
    """Show add prompt tab"""
    st.subheader("➕ 새 프롬프트 추가")
    
    with st.form("add_form"):
        title = st.text_input("프롬프트 제목")
        prompt = st.text_area("프롬프트 내용")
        category = st.selectbox("분야", CATEGORIES)
        tool = st.text_input("도구 이름 (예: React, FastAPI)")
        framework = st.text_input("프레임워크 이름 (예: Next.js, Streamlit)")
        level = st.selectbox("레벨", LEVELS)
        keywords = st.text_input("키워드 (쉼표로 구분)")
        
        submitted = st.form_submit_button("저장")
        
        if submitted:
            # 입력 검증
            keywords_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
            is_valid, error_msg = validate_prompt_input(title, prompt, keywords_list)
            
            if not is_valid:
                st.error(error_msg)
            else:
                new_prompt = prompt_service.add_prompt(
                    title=title,
                    prompt=prompt,
                    category=category,
                    tool=tool,
                    framework=framework,
                    level=level,
                    keywords=keywords_list
                )
                
                if new_prompt:
                    # 캐시 무효화
                    recommendation_service.invalidate_cache()
                    st.success("프롬프트가 저장되었습니다.")
                    st.cache_data.clear()
                else:
                    st.error("프롬프트 저장 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main()