import unittest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the src directory to sys.path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_dir)

# Import services and utilities
from services.prompt_service import PromptService
from services.recommendation_service import RecommendationService
from utils.helpers import filter_prompts, sort_prompts, validate_prompt_input
from utils.config import MAX_PROMPT_LENGTH, MAX_KEYWORD_LENGTH

class TestRecommendationService(unittest.TestCase):
    """Test recommendation service"""
    
    def setUp(self):
        self.recommendation_service = RecommendationService()

    # Test cases for extract_tags

    def test_extract_tags_empty_input(self):
        self.assertEqual(self.recommendation_service.extract_tags(""), {"categories": [], "keywords": []})

    def test_extract_tags_no_match(self):
        self.assertEqual(self.recommendation_service.extract_tags("some random text"), {"categories": [], "keywords": []})

    def test_extract_tags_single_keyword_one_category(self):
        # Assuming 'react' is in '프론트엔드'
        expected = {"categories": ["프론트엔드"], "keywords": ["react"]}
        self.assertEqual(self.recommendation_service.extract_tags("I want to use react"), expected)

    def test_extract_tags_multiple_keywords_one_category(self):
        # Assuming 'react', 'ui' are in '프론트엔드'
        expected = {"categories": ["프론트엔드"], "keywords": ["react", "ui"]}
        # Order of keywords in expected output is sorted
        self.assertEqual(self.recommendation_service.extract_tags("I want to use react and ui"), expected)

    def test_extract_tags_keywords_multiple_categories(self):
        # Assuming 'react' in '프론트엔드' and 'api' in '백엔드'
        expected = {"categories": ["백엔드", "프론트엔드"], "keywords": ["api", "react"]}
        # Order of categories and keywords in expected output is sorted
        self.assertEqual(self.recommendation_service.extract_tags("Build a react app with an api"), expected)
    
    def test_extract_tags_case_insensitivity(self):
        expected = {"categories": ["프론트엔드"], "keywords": ["react"]}
        self.assertEqual(self.recommendation_service.extract_tags("I want to use REACT"), expected)

    def test_extract_tags_korean_keywords(self):
        expected = {"categories": ["AI/LLM"], "keywords": ["요약"]}
        self.assertEqual(self.recommendation_service.extract_tags("텍스트 요약 기능"), expected)
        
        expected_multi = {"categories": ["AI/LLM", "백엔드"], "keywords": ["api", "인증", "프롬프트"]}
        self.assertEqual(self.recommendation_service.extract_tags("LLM 프롬프트 인증 API"), expected_multi)

    # Test cases for recommend (keyword-based)

    def setUp(self):
        # Sample prompts for testing the recommend function
        self.sample_prompts = [
            {
                "id": "1", "title": "React Login Form", "prompt": "...", "category": "프론트엔드", 
                "tool": "React", "level": "중급", "keywords": ["react", "form", "login"] # Score with "react form": C(2) + K(2) = 4
            },
            {
                "id": "2", "title": "FastAPI Backend", "prompt": "...", "category": "백엔드", 
                "tool": "FastAPI", "level": "중급", "keywords": ["fastapi", "api", "server"] # Score with "fastapi server": C(2) + K(2) = 4
            },
            {
                "id": "3", "title": "React Component UI", "prompt": "...", "category": "프론트엔드", 
                "tool": "React", "level": "입문", "keywords": ["react", "ui", "component"] # Score with "react ui component": C(2) + K(3) = 5
            },
            {
                "id": "4", "title": "Python Basics", "prompt": "...", "category": "기초", 
                "tool": "Python", "level": "입문", "keywords": ["python", "basic", "loop"]
            },
            {
                "id": "5", "title": "Another React Component", "prompt": "...", "category": "프론트엔드",
                "tool": "React", "level": "고급", "keywords": ["react", "advanced", "component"] # Score with "react": C(2) + K(1) = 3
            }
        ]

    def test_recommend_no_match(self):
        tags = {"categories": ["DevOps"], "keywords": ["docker"]}
        self.assertEqual(self.recommendation_service.keyword_recommend(tags, self.sample_prompts), [])

    def test_recommend_single_perfect_match(self):
        # This test assumes extract_tags works correctly for "fastapi server"
        tags = self.recommendation_service.extract_tags("fastapi server") # Should give: {"categories": ["백엔드"], "keywords": ["fastapi", "server"]}
        results = self.recommendation_service.keyword_recommend(tags, self.sample_prompts)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "2")

    def test_recommend_multiple_matches_and_ordering(self):
        tags = self.recommendation_service.extract_tags("react ui component form") # Matches 프론트엔드 (cat), react, ui, component, form (keywords)
        # Prompt 1 ("React Login Form"): category "프론트엔드" (2) + keywords "react", "form" (2) = 4
        # Prompt 3 ("React Component UI"): category "프론트엔드" (2) + keywords "react", "ui", "component" (3) = 5
        # Prompt 5 ("Another React Component"): category "프론트엔드" (2) + "react", "component" (2) = 4
        
        results = self.recommendation_service.keyword_recommend(tags, self.sample_prompts, top_k=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["id"], "3") # Highest score 5
        
        # Prompts 1 and 5 have score 4. Their order might depend on original list or sort stability.
        self.assertIn(results[1]["id"], ["1", "5"])
        self.assertIn(results[2]["id"], ["1", "5"])
        self.assertNotEqual(results[1]["id"], results[2]["id"])


    def test_recommend_top_k_parameter(self):
        tags = self.recommendation_service.extract_tags("react") # Matches 프론트엔드, react. Prompts 1, 3, 5 match.
        # Scores: P1=3, P3=3, P5=3
        results_top_1 = self.recommendation_service.keyword_recommend(tags, self.sample_prompts, top_k=1)
        self.assertEqual(len(results_top_1), 1)
        self.assertIn(results_top_1[0]["id"], ["1", "3", "5"])

        results_top_2 = self.recommendation_service.keyword_recommend(tags, self.sample_prompts, top_k=2)
        self.assertEqual(len(results_top_2), 2)
        self.assertIn(results_top_2[0]["id"], ["1", "3", "5"])
        self.assertIn(results_top_2[1]["id"], ["1", "3", "5"])
        self.assertNotEqual(results_top_2[0]["id"], results_top_2[1]["id"])


    def test_recommend_scoring_logic_category_priority(self):
        # Prompt with category match only vs prompt with keyword match only
        custom_prompts = [
            {"id": "cat_only", "category": "프론트엔드", "keywords": ["unique_cat_kw"]}, # Score with "프론트엔드": 2
            {"id": "kw_only", "category": "기타", "keywords": ["프론트엔드", "another_kw"]}    # Score with "프론트엔드": 1
        ]
        tags = extract_tags("프론트엔드") # This will result in {"categories": ["프론트엔드"], "keywords": ["프론트엔드"]}
                                      # if "프론트엔드" is also a keyword in CATEGORY_KEYWORDS_DATA.
                                      # Let's assume "프론트엔드" is NOT a keyword itself for a category for this test's clarity.
                                      # So, tags will be {"categories": ["프론트엔드"], "keywords": []} if "프론트엔드" is not a keyword in any category values.
                                      # Or more simply, let's use a keyword that defines a category but isn't the category name.
        
        # Let's use "react" which defines "프론트엔드"
        tags_react = self.recommendation_service.extract_tags("react") # {"categories": ["프론트엔드"], "keywords": ["react"]}

        custom_prompts_for_react = [
             {
                "id": "cat_match_only_for_react", "category": "프론트엔드", "keywords": ["other"],
                # Score with tags_react: C(2) + K(0) = 2
            },
            {
                "id": "kw_match_only_for_react", "category": "기타", "keywords": ["react", "some_other_kw"],
                # Score with tags_react: C(0) + K(1) = 1
            },
             {
                "id": "both_match_for_react", "category": "프론트엔드", "keywords": ["react", "yet_another_kw"],
                # Score with tags_react: C(2) + K(1) = 3
            }
        ]
        
        results = self.recommendation_service.keyword_recommend(tags_react, custom_prompts_for_react, top_k=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["id"], "both_match_for_react") # Score 3
        self.assertEqual(results[1]["id"], "cat_match_only_for_react") # Score 2
        self.assertEqual(results[2]["id"], "kw_match_only_for_react") # Score 1
        
    def test_recommend_empty_tags(self):
        tags = {"categories": [], "keywords": []}
        results = self.recommendation_service.keyword_recommend(tags, self.sample_prompts)
        self.assertEqual(results, []) # No score should be > 0


class TestPromptService(unittest.TestCase):
    """Test prompt service operations."""
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        self.sample_data = [
            {
                "id": "1",
                "title": "Test Prompt",
                "prompt": "Test content",
                "category": "프론트엔드",
                "keywords": ["test", "prompt"]
            }
        ]
        
        self.prompt_service = PromptService(self.temp_file_path)
    
    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)
    
    def test_save_and_load_prompts(self):
        # Test saving
        result = self.prompt_service.save_prompts(self.sample_data)
        self.assertTrue(result)
        
        # Test loading
        loaded_data = self.prompt_service.load_prompts()
        self.assertEqual(loaded_data, self.sample_data)
    
    def test_load_prompts_file_not_found(self):
        nonexistent_service = PromptService("nonexistent.json")
        result = nonexistent_service.load_prompts()
        self.assertEqual(result, [])
    
    def test_save_prompts_invalid_file_path(self):
        invalid_service = PromptService("/invalid/path/file.json")
        result = invalid_service.save_prompts(self.sample_data)
        self.assertFalse(result)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions from utils.py."""
    
    def setUp(self):
        self.sample_prompts = [
            {
                "id": "1", "title": "React App", "category": "프론트엔드",
                "level": "중급", "tool": "React", "keywords": ["react", "app"]
            },
            {
                "id": "2", "title": "API Server", "category": "백엔드",
                "level": "고급", "tool": "FastAPI", "keywords": ["api", "server"]
            },
            {
                "id": "3", "title": "Basic Python", "category": "기초",
                "level": "입문", "tool": "Python", "keywords": ["python", "basic"]
            }
        ]
    
    def test_filter_prompts_by_category(self):
        filtered = filter_prompts(self.sample_prompts, categories=["프론트엔드"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "1")
    
    def test_filter_prompts_by_level(self):
        filtered = filter_prompts(self.sample_prompts, levels=["입문", "중급"])
        self.assertEqual(len(filtered), 2)
        self.assertIn(filtered[0]["id"], ["1", "3"])
        self.assertIn(filtered[1]["id"], ["1", "3"])
    
    def test_filter_prompts_by_search_query(self):
        filtered = filter_prompts(self.sample_prompts, search_query="python")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "3")
    
    def test_filter_prompts_multiple_criteria(self):
        filtered = filter_prompts(
            self.sample_prompts,
            categories=["프론트엔드", "백엔드"],
            levels=["중급", "고급"]
        )
        self.assertEqual(len(filtered), 2)
        
    def test_sort_prompts_by_title(self):
        sorted_prompts = sort_prompts(self.sample_prompts, "제목순")
        titles = [p["title"] for p in sorted_prompts]
        self.assertEqual(titles, ["API Server", "Basic Python", "React App"])
    
    def test_sort_prompts_by_level(self):
        sorted_prompts = sort_prompts(self.sample_prompts, "레벨순")
        levels = [p["level"] for p in sorted_prompts]
        self.assertEqual(levels, ["입문", "중급", "고급"])
    
    def test_validate_prompt_input_valid(self):
        is_valid, error = validate_prompt_input(
            "Test Title", "Test prompt content", ["test", "keyword"]
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_prompt_input_empty_title(self):
        is_valid, error = validate_prompt_input("", "Test content", ["test"])
        self.assertFalse(is_valid)
        self.assertIn("제목", error)
    
    def test_validate_prompt_input_empty_prompt(self):
        is_valid, error = validate_prompt_input("Title", "", ["test"])
        self.assertFalse(is_valid)
        self.assertIn("프롬프트 내용", error)
    
    def test_validate_prompt_input_too_long(self):
        long_prompt = "x" * (MAX_PROMPT_LENGTH + 1)
        is_valid, error = validate_prompt_input("Title", long_prompt, ["test"])
        self.assertFalse(is_valid)
        self.assertIn("너무 깁니다", error)
    
    def test_validate_prompt_input_long_keyword(self):
        long_keyword = "x" * (MAX_KEYWORD_LENGTH + 1)
        is_valid, error = validate_prompt_input(
            "Title", "Content", ["normal", long_keyword]
        )
        self.assertFalse(is_valid)
        self.assertIn("키워드가 너무", error)


class TestVectorOperations(unittest.TestCase):
    """Test vector-related operations."""
    
    def setUp(self):
        self.recommendation_service = RecommendationService()
    
    def test_get_prompt_text(self):
        prompt = {
            "title": "Test Title",
            "prompt": "Test content",
            "keywords": ["test", "keyword"]
        }
        result = self.recommendation_service._get_prompt_text(prompt)
        expected = "Test Title Test content test keyword"
        self.assertEqual(result, expected)
    
    def test_get_prompt_text_missing_fields(self):
        prompt = {"title": "Test Title"}
        result = self.recommendation_service._get_prompt_text(prompt)
        expected = "Test Title  "
        self.assertEqual(result, expected)
    
    def test_vector_recommend_empty_prompts(self):
        result = self.recommendation_service.vector_recommend("test query", [])
        self.assertEqual(result, [])
    
    def test_vector_recommend_empty_input(self):
        prompts = [{"id": "1", "title": "Test"}]
        result = self.recommendation_service.vector_recommend("", prompts)
        self.assertEqual(result, [])
    
    def test_hybrid_recommend_empty_inputs(self):
        result = self.recommendation_service.hybrid_recommend("", [])
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
