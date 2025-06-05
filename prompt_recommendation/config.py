"""Configuration for Prompt Recommendation System"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PROMPTS_TABLE = "prompts"

# Model settings
EMBEDDING_MODEL = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"

# UI settings
ITEMS_PER_PAGE = 10

# Categories and levels
CATEGORIES = ["AI/LLM", "백엔드", "프론트엔드", "데이터분석", "자동화", "기타"]
LEVELS = ["입문", "중급", "고급"]

# Recommendation weights
KEYWORD_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6