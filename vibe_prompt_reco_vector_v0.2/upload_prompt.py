import json
import os
import sys
import logging
from pathlib import Path
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            logger.error("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
            sys.exit(1)
        
        supabase: Client = create_client(url, key)
        
        script_dir = Path(__file__).parent
        prompts_file = script_dir / "data" / "prompts.json"
        
        if not prompts_file.exists():
            logger.error(f"Prompts file not found: {prompts_file}")
            sys.exit(1)
        
        with open(prompts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        logger.info(f"Uploading {len(data)} prompts to Supabase...")
        
        for i, item in enumerate(data, 1):
            try:
                result = supabase.table("prompts").upsert(item).execute()
                if i % 10 == 0:
                    logger.info(f"Uploaded {i}/{len(data)} prompts")
            except Exception as e:
                logger.error(f"Failed to upload prompt {i}: {e}")
                continue
        
        logger.info("Upload completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()