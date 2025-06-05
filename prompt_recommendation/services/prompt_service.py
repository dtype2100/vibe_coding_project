"""Prompt management service with Supabase integration"""

import os
import json
from typing import List, Dict, Any, Optional
from uuid import uuid4
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


class PromptService:
    """Service for managing prompts with Supabase"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            self.supabase: Client = create_client(url, key)
        else:
            logger.warning("Supabase credentials not found")
            self.supabase = None
    
    def load_prompts(self) -> List[Dict[str, Any]]:
        """Load prompts from Supabase or local fallback"""
        # Try Supabase first
        if self.supabase:
            try:
                response = self.supabase.table("prompts").select("*").execute()
                if response.data:
                    return response.data
            except Exception as e:
                logger.error(f"Supabase error: {e}")
        
        # Fallback to local JSON
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "prompts.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else data.get("prompts", [])
            except Exception as e:
                logger.error(f"Local file error: {e}")
        
        return []
    
    def add_prompt(self, title: str, prompt: str, category: str, 
                   tool: str = "", level: str = "중급", 
                   keywords: List[str] = None) -> Optional[Dict[str, Any]]:
        """Add new prompt to Supabase"""
        if not self.supabase:
            return None
            
        new_prompt = {
            "id": str(uuid4()),
            "title": title.strip(),
            "prompt": prompt.strip(),
            "category": category,
            "tool": tool.strip(),
            "level": level,
            "keywords": keywords or []
        }
        
        try:
            result = self.supabase.table("prompts").insert(new_prompt).execute()
            return new_prompt if result.data else None
        except Exception as e:
            logger.error(f"Failed to add prompt: {e}")
            return None