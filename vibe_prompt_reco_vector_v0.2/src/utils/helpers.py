"""
Utility functions for Vibe Prompt Manager
"""

from typing import List, Dict, Any, Optional
import streamlit as st
from utils.config import CATEGORIES, LEVELS, TOOLS, MAX_PROMPT_LENGTH, MAX_KEYWORD_LENGTH


def filter_prompts(
    prompts: List[Dict[str, Any]],
    categories: Optional[List[str]] = None,
    levels: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter prompts based on multiple criteria.
    
    Args:
        prompts: List of prompt dictionaries
        categories: List of categories to filter by
        levels: List of levels to filter by
        tools: List of tools to filter by
        search_query: Search string to filter prompts
        
    Returns:
        Filtered list of prompts
    """
    filtered = prompts
    
    if categories:
        filtered = [p for p in filtered if p.get("category") in categories]
    
    if levels:
        filtered = [p for p in filtered if p.get("level") in levels]
    
    if tools:
        filtered = [p for p in filtered if p.get("tool") in tools]
    
    if search_query:
        query_lower = search_query.lower()
        filtered = [
            p for p in filtered
            if query_lower in p.get("title", "").lower()
            or query_lower in p.get("prompt", "").lower()
            or any(query_lower in kw.lower() for kw in p.get("keywords", []))
        ]
    
    return filtered


def sort_prompts(
    prompts: List[Dict[str, Any]], 
    sort_by: str = "최신순"
) -> List[Dict[str, Any]]:
    """
    Sort prompts based on specified criteria.
    
    Args:
        prompts: List of prompt dictionaries
        sort_by: Sort criteria ("최신순", "제목순", "분야순", "레벨순")
        
    Returns:
        Sorted list of prompts
    """
    if sort_by == "최신순":
        return prompts[::-1]  # 최신 추가된 순
    
    elif sort_by == "제목순":
        return sorted(prompts, key=lambda x: x.get("title", ""))
    
    elif sort_by == "분야순":
        return sorted(prompts, key=lambda x: (x.get("category", ""), x.get("title", "")))
    
    elif sort_by == "레벨순":
        level_order = {"입문": 0, "중급": 1, "고급": 2}
        return sorted(
            prompts, 
            key=lambda x: (level_order.get(x.get("level", ""), 0), x.get("title", ""))
        )
    
    return prompts


def display_prompt_card(prompt: Dict[str, Any]) -> None:
    """
    Display a single prompt in a formatted card.
    
    Args:
        prompt: Prompt dictionary to display
    """
    st.markdown(f"**{prompt.get('title', '제목 없음')}**")
    st.code(prompt.get("prompt", ""), language="text")
    
    info_parts = [
        f"분야: `{prompt.get('category', 'N/A')}`",
        f"도구: `{prompt.get('tool', 'N/A')}`",
        f"레벨: `{prompt.get('level', 'N/A')}`"
    ]
    
    if 'similarity_score' in prompt:
        info_parts.append(f"유사도: `{prompt['similarity_score']:.3f}`")
    
    st.markdown(" / ".join(info_parts))
    st.markdown("---")


def display_prompt_detail(prompt: Dict[str, Any]) -> None:
    """
    Display detailed prompt information in expandable format.
    
    Args:
        prompt: Prompt dictionary to display
    """
    with st.expander(f"### {prompt.get('title', '제목 없음')}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**프롬프트 내용**")
            st.code(prompt.get("prompt", ""), language="text")
        
        with col2:
            st.markdown("**메타데이터**")
            st.markdown(f"📌 분야: `{prompt.get('category', 'N/A')}`")
            st.markdown(f"🛠️ 도구: `{prompt.get('tool', 'N/A')}`")
            st.markdown(f"📚 프레임워크: `{prompt.get('framework', 'N/A')}`")
            st.markdown(f"⭐ 레벨: `{prompt.get('level', 'N/A')}`")
            st.markdown("🔑 키워드:")
            for kw in prompt.get("keywords", []):
                st.markdown(f"- `{kw}`")
    
    st.markdown("---")


def validate_prompt_input(
    title: str,
    prompt: str,
    keywords: List[str]
) -> tuple[bool, Optional[str]]:
    """
    Validate prompt input fields.
    
    Args:
        title: Prompt title
        prompt: Prompt content
        keywords: List of keywords
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "제목을 입력해주세요."
    
    if not prompt or not prompt.strip():
        return False, "프롬프트 내용을 입력해주세요."
    
    if len(prompt) > MAX_PROMPT_LENGTH:
        return False, f"프롬프트가 너무 깁니다. {MAX_PROMPT_LENGTH}자 이내로 입력해주세요."
    
    if any(len(kw) > MAX_KEYWORD_LENGTH for kw in keywords):
        return False, f"키워드가 너무 깁니다. 각 키워드는 {MAX_KEYWORD_LENGTH}자 이내로 입력해주세요."
    
    return True, None