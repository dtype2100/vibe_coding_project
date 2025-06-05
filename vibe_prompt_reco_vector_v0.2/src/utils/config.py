"""
Configuration settings for Vibe Prompt Manager
"""

import os

# Search weights
KEYWORD_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6

# UI settings
ITEMS_PER_PAGE = 10

# File paths
DB_FILE = "prompts.json"
ADDITIONAL_PROMPTS_FILE = "additional_prompts.json"
TRENDING_PROMPTS_FILE = "trending_prompts.json"
ALL_PROMPTS_FILE = "all_prompts_combined.json"
EMBEDDING_CACHE_FILE = "embeddings_cache.pkl"

# Model settings
EMBEDDING_MODEL_NAME = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"

# Cache settings
CACHE_ENABLED = True
CACHE_EXPIRY_DAYS = 7

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Categories
CATEGORIES = [
    "Document Creation",
    "Research and Analysis", 
    "Communication",
    "Creative Tasks",
    "Data and Analytics",
    "Programming and Development",
    "Problem Solving",
    "Education and Training",
    "Content Generation",
    "Business Strategy"
]

# Difficulty levels
LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]

# Tools
TOOLS = [
    "ChatGPT",
    "Claude",
    "Gemini",
    "Copilot",
    "Perplexity",
    "GPT-4",
    "Dall-E",
    "Midjourney"
]

# Input validation settings
MAX_PROMPT_LENGTH = 2000
MAX_KEYWORD_LENGTH = 50

# Supabase settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PROMPTS_TABLE = "prompts"