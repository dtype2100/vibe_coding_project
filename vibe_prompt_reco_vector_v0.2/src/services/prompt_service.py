"""
Prompt management service
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from uuid import uuid4
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class PromptService:
    """Service for managing prompts (CRUD operations) - supabase only"""
    def __init__(self, data_path: str = None):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            logger.error("SUPABASE_URL and SUPABASE_KEY 환경변수가 필요합니다.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(url, key)

    def load_prompts(self) -> List[Dict[str, Any]]:
        """Supabase에서 prompt 데이터를 읽어옴. 실패 시 로컬 파일에서 읽음."""
        # Supabase에서 데이터 읽기 시도
        if self.supabase:
            try:
                response = self.supabase.table("prompts").select("*").execute()
                data = response.data
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception as e:
                logger.error(f"Supabase에서 프롬프트를 불러오는 중 오류 발생: {e}")
        
        # 로컬 JSON 파일에서 읽기 (폴백)
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "prompts.json")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "prompts" in data:
                        return data["prompts"]
            except Exception as e:
                logger.error(f"로컬 파일 읽기 오류: {e}")
        
        return []

    def add_prompt(
        self,
        title: str,
        prompt: str,
        category: str,
        tool: str = "",
        framework: str = "",
        level: str = "중급",
        keywords: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Supabase에 새 프롬프트 추가"""
        if not self.supabase:
            return None
        if keywords is None:
            keywords = []
        new_prompt = {
            "id": str(uuid4()),
            "title": title.strip(),
            "prompt": prompt.strip(),
            "category": category,
            "tool": tool.strip() if tool else "",
            "framework": framework.strip() if framework else "",
            "level": level,
            "keywords": keywords
        }
        try:
            result = self.supabase.table("prompts").insert(new_prompt).execute()
            return new_prompt if result.data else None
        except Exception as e:
            logger.error(f"Supabase에 프롬프트 추가 중 오류 발생: {e}")
            return None

    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """ID로 프롬프트 조회 (supabase)"""
        if not self.supabase:
            return None
        try:
            response = self.supabase.table("prompts").select("*").eq("id", prompt_id).single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Supabase에서 프롬프트 단건 조회 오류: {e}")
            return None

    def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> bool:
        """프롬프트 수정 (supabase)"""
        if not self.supabase:
            return False
        try:
            result = self.supabase.table("prompts").update(updates).eq("id", prompt_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Supabase에서 프롬프트 수정 오류: {e}")
            return False

    def delete_prompt(self, prompt_id: str) -> bool:
        """프롬프트 삭제 (supabase)"""
        if not self.supabase:
            return False
        try:
            result = self.supabase.table("prompts").delete().eq("id", prompt_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Supabase에서 프롬프트 삭제 오류: {e}")
            return False

