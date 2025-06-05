"""
Data models for the prompt recommendation system
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Prompt:
    """Data model for a prompt"""
    id: str
    title: str
    prompt: str
    category: str
    level: str
    keywords: List[str]
    tool: Optional[str] = ""
    framework: Optional[str] = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "prompt": self.prompt,
            "category": self.category,
            "level": self.level,
            "keywords": self.keywords,
            "tool": self.tool,
            "framework": self.framework,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Prompt':
        """Create from dictionary"""
        created_at = None
        updated_at = None
        
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        return cls(
            id=data["id"],
            title=data["title"],
            prompt=data["prompt"],
            category=data["category"],
            level=data["level"],
            keywords=data.get("keywords", []),
            tool=data.get("tool", ""),
            framework=data.get("framework", ""),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class RecommendationResult:
    """Data model for recommendation results"""
    prompt: Prompt
    score: float
    similarity_score: Optional[float] = None
    recommendation_type: str = "hybrid"  # keyword, vector, hybrid
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        result = self.prompt.to_dict()
        result.update({
            "score": self.score,
            "recommendation_type": self.recommendation_type
        })
        if self.similarity_score is not None:
            result["similarity_score"] = self.similarity_score
        return result


@dataclass
class SearchFilter:
    """Data model for search filters"""
    categories: Optional[List[str]] = None
    levels: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    search_query: Optional[str] = None
    sort_by: str = "최신순"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "categories": self.categories,
            "levels": self.levels,
            "tools": self.tools,
            "search_query": self.search_query,
            "sort_by": self.sort_by
        }