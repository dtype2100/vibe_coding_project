#!/usr/bin/env python3
"""
Script to merge and deduplicate prompt data files
"""

import json
import os
import sys
from typing import List, Dict, Any, Set

def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON file and return data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return []

def normalize_prompt(prompt: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize prompt data structure"""
    normalized = {
        "id": prompt.get("id", ""),
        "title": prompt.get("title", ""),
        "prompt": prompt.get("prompt", ""),
        "category": prompt.get("category", ""),
        "tool": prompt.get("tool", ""),
        "framework": prompt.get("framework", ""),
        "level": prompt.get("level", "중급"),
        "keywords": prompt.get("keywords", [])
    }
    
    # Ensure keywords is a list
    if isinstance(normalized["keywords"], str):
        normalized["keywords"] = [normalized["keywords"]]
    elif not isinstance(normalized["keywords"], list):
        normalized["keywords"] = []
    
    return normalized

def find_duplicates(prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates based on title and content similarity"""
    seen_titles: Set[str] = set()
    seen_contents: Set[str] = set()
    unique_prompts = []
    
    for prompt in prompts:
        title = prompt.get("title", "").strip().lower()
        content = prompt.get("prompt", "").strip().lower()
        
        # Skip if title or content is empty
        if not title or not content:
            continue
        
        # Check for exact title match
        if title in seen_titles:
            print(f"Duplicate title found: {prompt.get('title')}")
            continue
        
        # Check for exact content match
        if content in seen_contents:
            print(f"Duplicate content found for: {prompt.get('title')}")
            continue
        
        seen_titles.add(title)
        seen_contents.add(content)
        unique_prompts.append(prompt)
    
    return unique_prompts

def merge_data_files() -> None:
    """Merge all data files and remove duplicates"""
    data_dir = "data"
    
    # Define file paths
    files_to_merge = [
        "vibe_prompts_structured_upgraded.json",
        "additional_prompts.json", 
        "trending_prompts.json"
    ]
    
    all_prompts = []
    
    # Load data from all files
    for filename in files_to_merge:
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
            print(f"Loading {filename}...")
            data = load_json_file(file_path)
            print(f"  - Loaded {len(data)} prompts")
            
            # Normalize and add to all_prompts
            for prompt in data:
                normalized = normalize_prompt(prompt)
                if normalized["id"] and normalized["title"] and normalized["prompt"]:
                    all_prompts.append(normalized)
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nTotal prompts before deduplication: {len(all_prompts)}")
    
    # Remove duplicates
    unique_prompts = find_duplicates(all_prompts)
    print(f"Total prompts after deduplication: {len(unique_prompts)}")
    print(f"Removed {len(all_prompts) - len(unique_prompts)} duplicates")
    
    # Sort by category and title
    unique_prompts.sort(key=lambda x: (x.get("category", ""), x.get("title", "")))
    
    # Save merged data
    output_file = os.path.join(data_dir, "prompts.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_prompts, f, indent=2, ensure_ascii=False)
        print(f"\nMerged data saved to: {output_file}")
        
        # Update config to use new file
        update_config_file()
        
    except Exception as e:
        print(f"Error saving merged data: {e}")

def update_config_file() -> None:
    """Update config file to use the new merged data file"""
    config_path = "src/utils/config.py"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace DB_FILE
        updated_content = content.replace(
            'DB_FILE = "vibe_prompts_structured_upgraded.json"',
            'DB_FILE = "prompts.json"'
        )
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Updated config file: {config_path}")
        
    except Exception as e:
        print(f"Error updating config file: {e}")

def print_statistics(prompts: List[Dict[str, Any]]) -> None:
    """Print statistics about the merged data"""
    print("\n=== Data Statistics ===")
    print(f"Total prompts: {len(prompts)}")
    
    # Category distribution
    categories = {}
    levels = {}
    tools = {}
    
    for prompt in prompts:
        cat = prompt.get("category", "Unknown")
        level = prompt.get("level", "Unknown")
        tool = prompt.get("tool", "Unknown")
        
        categories[cat] = categories.get(cat, 0) + 1
        levels[level] = levels.get(level, 0) + 1
        tools[tool] = tools.get(tool, 0) + 1
    
    print("\nCategories:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    print("\nLevels:")
    for level, count in sorted(levels.items()):
        print(f"  {level}: {count}")
    
    print("\nTop Tools:")
    sorted_tools = sorted(tools.items(), key=lambda x: x[1], reverse=True)
    for tool, count in sorted_tools[:10]:
        if tool and tool != "Unknown":
            print(f"  {tool}: {count}")

if __name__ == "__main__":
    print("Starting data merge process...")
    merge_data_files()
    
    # Load and print statistics
    merged_data = load_json_file("data/prompts.json")
    if merged_data:
        print_statistics(merged_data)
    
    print("\nData merge completed!")