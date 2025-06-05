"""
Recommendation service for prompt recommendations
"""

import logging
import os
import pickle
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating prompt recommendations"""
    
    def __init__(
        self, 
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        cache_file: str = "embeddings_cache.pkl"
    ):
        self.model_name = model_name
        self.cache_file = cache_file
        self.model = None
        self._category_keywords = {
            "프론트엔드": ["ui", "폼", "리액트", "react", "tailwind", "상태", "프론트"],
            "백엔드": ["api", "로그인", "fastapi", "서버", "rest", "인증"],
            "AI/LLM": ["gpt", "llm", "요약", "langchain", "llama", "프롬프트"],
            "데이터분석": ["pandas", "시각화", "csv", "plotly", "분석", "데이터"],
            "DevOps": ["docker", "배포", "ci", "github actions"],
            "기초": ["홀수", "짝수", "기초", "python", "입문"]
        }
    
    def _load_model(self) -> SentenceTransformer:
        """Load and cache the sentence transformer model"""
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self.model
    
    def extract_tags(self, text: str) -> Dict[str, List[str]]:
        """Extract categories and keywords from user input"""
        if not text:
            return {"categories": [], "keywords": []}
        
        text_lower = text.lower()
        matched_categories = []
        matched_keywords = []
        
        for category, keywords in self._category_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    matched_categories.append(category)
                    matched_keywords.append(kw)
        
        return {
            "categories": sorted(set(matched_categories)),
            "keywords": sorted(set(matched_keywords))
        }
    
    def keyword_recommend(
        self, 
        tags: Dict[str, List[str]], 
        prompts: List[Dict[str, Any]], 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Keyword-based prompt recommendation"""
        if not prompts or not tags:
            return []
        
        scored = []
        for prompt in prompts:
            score = 0
            if prompt.get("category") in tags["categories"]:
                score += 2
            score += len(set(tags["keywords"]) & set(prompt.get("keywords", [])))
            if score > 0:
                scored.append((score, prompt))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [item for _, item in scored[:min(top_k, len(scored))]]
    
    def _get_prompt_text(self, prompt: Dict[str, Any]) -> str:
        """Convert prompt to text for embedding"""
        return f"{prompt.get('title', '')} {prompt.get('prompt', '')} {' '.join(prompt.get('keywords', []))}"
    
    def _build_vector_index(
        self, 
        prompts: List[Dict[str, Any]]
    ) -> Tuple[Optional[faiss.Index], Optional[np.ndarray]]:
        """Build or load vector index for prompts"""
        if not prompts:
            return None, None
        
        try:
            model = self._load_model()
        except Exception as e:
            logger.error(f"Failed to load model for indexing: {e}")
            return None, None
        
        # Check for cached embeddings
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    if len(cached_data.get('prompts', [])) == len(prompts):
                        return cached_data['index'], cached_data['embeddings']
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
        
        # Generate prompt texts
        prompt_texts = [self._get_prompt_text(prompt) for prompt in prompts]
        
        # Generate embeddings
        embeddings = model.encode(prompt_texts, convert_to_numpy=True)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
        
        # Normalize and add to index
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))
        
        # Save cache
        try:
            cache_data = {
                'index': index,
                'embeddings': embeddings,
                'prompts': prompts
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
        
        return index, embeddings
    
    def vector_recommend(
        self, 
        user_input: str, 
        prompts: List[Dict[str, Any]], 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Vector-based prompt recommendation using semantic similarity"""
        if not prompts or not user_input:
            return []
        
        try:
            model = self._load_model()
            index, embeddings = self._build_vector_index(prompts)
            
            if index is None or embeddings is None:
                logger.error("Failed to build vector index")
                return []
            
            # Convert user input to embedding
            query_embedding = model.encode([user_input], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            # Similarity search
            scores, indices = index.search(query_embedding.astype('float32'), min(top_k, len(prompts)))
            
            # Return results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if 0 <= idx < len(prompts):
                    prompt = prompts[idx].copy()
                    prompt['similarity_score'] = float(score)
                    results.append(prompt)
            
            return results
        except Exception as e:
            logger.error(f"Error in vector recommendation: {e}")
            return []
    
    def hybrid_recommend(
        self, 
        user_input: str, 
        prompts: List[Dict[str, Any]], 
        top_k: int = 3,
        keyword_weight: float = 0.4,
        vector_weight: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Hybrid recommendation combining keyword and vector similarity"""
        if not prompts or not user_input:
            return []
        
        try:
            # Keyword-based results
            keyword_results = self.keyword_recommend(
                self.extract_tags(user_input), 
                prompts, 
                top_k * 2
            )
            
            # Vector-based results
            vector_results = self.vector_recommend(user_input, prompts, top_k * 2)
            
            # Combine results and remove duplicates
            combined = {}
            
            # Keyword results (weighted)
            for i, item in enumerate(keyword_results):
                item_id = item.get('id')
                if item_id:
                    score = (len(keyword_results) - i) * keyword_weight
                    combined[item_id] = {'item': item, 'score': score}
            
            # Vector results (weighted)
            for i, item in enumerate(vector_results):
                item_id = item.get('id')
                if item_id:
                    vector_score = item.get('similarity_score', 0) * vector_weight
                    
                    if item_id in combined:
                        combined[item_id]['score'] += vector_score
                    else:
                        combined[item_id] = {'item': item, 'score': vector_score}
            
            # Sort by score
            sorted_results = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
            
            return [result['item'] for result in sorted_results[:top_k]]
        except Exception as e:
            logger.error(f"Error in hybrid recommendation: {e}")
            return []
    
    def invalidate_cache(self) -> None:
        """Remove the embedding cache file"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("Cache invalidated")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")