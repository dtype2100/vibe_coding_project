import unittest
import sys
import os

# Add the directory of the script to be tested to sys.path
# This allows importing from vibe_prompt_manager_with_vector.py
script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vibe_prompt_reco_vector_v0.2'))
sys.path.insert(0, script_dir)

# Now import the functions and constants
from vibe_prompt_manager_with_vector import extract_tags, recommend, CATEGORY_KEYWORDS_DATA

class TestPromptManager(unittest.TestCase):

    # Test cases for extract_tags

    def test_extract_tags_empty_input(self):
        self.assertEqual(extract_tags(""), {"categories": [], "keywords": []})

    def test_extract_tags_no_match(self):
        self.assertEqual(extract_tags("some random text"), {"categories": [], "keywords": []})

    def test_extract_tags_single_keyword_one_category(self):
        # Assuming 'react' is in '프론트엔드'
        expected = {"categories": ["프론트엔드"], "keywords": ["react"]}
        self.assertEqual(extract_tags("I want to use react"), expected)

    def test_extract_tags_multiple_keywords_one_category(self):
        # Assuming 'react', 'ui' are in '프론트엔드'
        expected = {"categories": ["프론트엔드"], "keywords": ["react", "ui"]}
        # Order of keywords in expected output is sorted
        self.assertEqual(extract_tags("I want to use react and ui"), expected)

    def test_extract_tags_keywords_multiple_categories(self):
        # Assuming 'react' in '프론트엔드' and 'api' in '백엔드'
        expected = {"categories": ["백엔드", "프론트엔드"], "keywords": ["api", "react"]}
        # Order of categories and keywords in expected output is sorted
        self.assertEqual(extract_tags("Build a react app with an api"), expected)
    
    def test_extract_tags_case_insensitivity(self):
        expected = {"categories": ["프론트엔드"], "keywords": ["react"]}
        self.assertEqual(extract_tags("I want to use REACT"), expected)

    def test_extract_tags_korean_keywords(self):
        expected = {"categories": ["AI/LLM"], "keywords": ["요약"]}
        self.assertEqual(extract_tags("텍스트 요약 기능"), expected)
        
        expected_multi = {"categories": ["AI/LLM", "백엔드"], "keywords": ["api", "인증", "프롬프트"]}
        self.assertEqual(extract_tags("LLM 프롬프트 인증 API"), expected_multi)

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
        self.assertEqual(recommend(tags, self.sample_prompts), [])

    def test_recommend_single_perfect_match(self):
        # This test assumes extract_tags works correctly for "fastapi server"
        tags = extract_tags("fastapi server") # Should give: {"categories": ["백엔드"], "keywords": ["fastapi", "server"]}
        results = recommend(tags, self.sample_prompts)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "2")

    def test_recommend_multiple_matches_and_ordering(self):
        tags = extract_tags("react ui component form") # Matches 프론트엔드 (cat), react, ui, component, form (keywords)
        # Prompt 1 ("React Login Form"): category "프론트엔드" (2) + keywords "react", "form" (2) = 4
        # Prompt 3 ("React Component UI"): category "프론트엔드" (2) + keywords "react", "ui", "component" (3) = 5
        # Prompt 5 ("Another React Component"): category "프론트엔드" (2) + "react", "component" (2) = 4
        
        results = recommend(tags, self.sample_prompts, top_k=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["id"], "3") # Highest score 5
        
        # Prompts 1 and 5 have score 4. Their order might depend on original list or sort stability.
        self.assertIn(results[1]["id"], ["1", "5"])
        self.assertIn(results[2]["id"], ["1", "5"])
        self.assertNotEqual(results[1]["id"], results[2]["id"])


    def test_recommend_top_k_parameter(self):
        tags = extract_tags("react") # Matches 프론트엔드, react. Prompts 1, 3, 5 match.
        # Scores: P1=3, P3=3, P5=3
        results_top_1 = recommend(tags, self.sample_prompts, top_k=1)
        self.assertEqual(len(results_top_1), 1)
        self.assertIn(results_top_1[0]["id"], ["1", "3", "5"])

        results_top_2 = recommend(tags, self.sample_prompts, top_k=2)
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
        tags_react = extract_tags("react") # {"categories": ["프론트엔드"], "keywords": ["react"]}

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
        
        results = recommend(tags_react, custom_prompts_for_react, top_k=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["id"], "both_match_for_react") # Score 3
        self.assertEqual(results[1]["id"], "cat_match_only_for_react") # Score 2
        self.assertEqual(results[2]["id"], "kw_match_only_for_react") # Score 1
        
    def test_recommend_empty_tags(self):
        tags = {"categories": [], "keywords": []}
        results = recommend(tags, self.sample_prompts)
        self.assertEqual(results, []) # No score should be > 0

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
