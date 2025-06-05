"""Recommendation service with keyword and vector search"""

import os
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for prompt recommendations"""
    
    def __init__(self, cache_file: str = "embeddings_cache.pkl"):
        self.cache_file = cache_file
        self.model_name = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"
        self.model = None
        self._embeddings_cache = {}
        
        # Category keywords for better matching
        self.category_keywords = {
            "AI/LLM": ["ai", "llm", "gpt", "claude", "llama", "langchain", "embedding", "vector"],
            "백엔드": ["backend", "api", "server", "database", "fastapi", "django", "flask"],
            "프론트엔드": ["frontend", "react", "vue", "javascript", "css", "html", "ui"],
            "데이터분석": ["data", "pandas", "numpy", "matplotlib", "plotly", "csv", "분석"],
            "자동화": ["automation", "script", "bot", "crawling", "selenium", "자동화"]
        }
    
    def _load_model(self):
        """Lazy load the embedding model"""
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise
        return self.model
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract relevant keywords from user input"""
        if not text:
            return []
        
        text_lower = text.lower()
        tags = []
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.append(keyword)
                    
        return list(set(tags))
    
    def keyword_recommend(self, user_input: str, prompts: List[Dict[str, Any]], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword-based recommendation"""
        if not prompts or not user_input:
            return []
        
        tags = self.extract_tags(user_input)
        user_words = set(user_input.lower().split())
        
        scored_prompts = []
        for prompt in prompts:
            score = 0
            
            # Check title and prompt content
            if any(word in prompt.get("title", "").lower() for word in user_words):
                score += 2
            if any(word in prompt.get("prompt", "").lower() for word in user_words):
                score += 1
                
            # Check keywords
            prompt_keywords = [kw.lower() for kw in prompt.get("keywords", [])]
            score += len(set(tags) & set(prompt_keywords))
            
            if score > 0:
                scored_prompts.append((score, prompt))
        
        scored_prompts.sort(key=lambda x: x[0], reverse=True)
        return [p[1] for p in scored_prompts[:top_k]]
    
    def _build_vector_index(self, prompts: List[Dict[str, Any]]) -> Optional[faiss.Index]:
        """Build FAISS index for vector search"""
        if not prompts:
            return None
            
        # Check cache
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                    if len(cache.get('prompts', [])) == len(prompts):
                        return cache['index']
            except:
                pass
        
        # Build new index
        try:
            model = self._load_model()
            texts = [f"{p.get('title', '')} {p.get('prompt', '')} {' '.join(p.get('keywords', []))}" 
                    for p in prompts]
            
            embeddings = model.encode(texts, convert_to_numpy=True)
            
            # Create index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            
            # Normalize and add
            faiss.normalize_L2(embeddings)
            index.add(embeddings.astype('float32'))
            
            # Save cache
            with open(self.cache_file, 'wb') as f:
                pickle.dump({'index': index, 'prompts': prompts}, f)
                
            return index
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            return None
    
    def vector_recommend(self, user_input: str, prompts: List[Dict[str, Any]], 
                        top_k: int = 5) -> List[Dict[str, Any]]:
        """Vector similarity based recommendation"""
        if not prompts or not user_input:
            return []
            
        index = self._build_vector_index(prompts)
        if index is None:
            return self.keyword_recommend(user_input, prompts, top_k)
        
        try:
            model = self._load_model()
            query_embedding = model.encode([user_input], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            distances, indices = index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(prompts):
                    prompt = prompts[idx].copy()
                    prompt['similarity_score'] = float(distances[0][i])
                    results.append(prompt)
                    
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return self.keyword_recommend(user_input, prompts, top_k)
    
    def hybrid_recommend(self, user_input: str, prompts: List[Dict[str, Any]], 
                        top_k: int = 5) -> List[Dict[str, Any]]:
        """Hybrid recommendation combining keyword and vector search"""
        keyword_results = self.keyword_recommend(user_input, prompts, top_k * 2)
        vector_results = self.vector_recommend(user_input, prompts, top_k * 2)
        
        # Merge and rank
        seen_ids = set()
        merged = []
        
        # Add all results with scores
        for i, prompt in enumerate(keyword_results):
            prompt_id = prompt.get('id')
            if prompt_id not in seen_ids:
                seen_ids.add(prompt_id)
                prompt['keyword_rank'] = i + 1
                prompt['vector_rank'] = 999
                merged.append(prompt)
        
        for i, prompt in enumerate(vector_results):
            prompt_id = prompt.get('id')
            if prompt_id in seen_ids:
                # Update existing
                for p in merged:
                    if p.get('id') == prompt_id:
                        p['vector_rank'] = i + 1
                        break
            else:
                seen_ids.add(prompt_id)
                prompt['keyword_rank'] = 999
                prompt['vector_rank'] = i + 1
                merged.append(prompt)
        
        # Calculate final score
        for prompt in merged:
            keyword_score = 1 / prompt.get('keyword_rank', 999)
            vector_score = 1 / prompt.get('vector_rank', 999)
            prompt['final_score'] = (0.4 * keyword_score + 0.6 * vector_score)
        
        merged.sort(key=lambda x: x['final_score'], reverse=True)
        return merged[:top_k]