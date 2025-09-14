from enum import Enum
import os
import sys

class Keys(Enum):
    tg_client_api_id = "TG_API_ID"
    tg_client_api_hash = "TG_API_HASH"
    tg_bot_token_bydlan = "TG_BOT_TOKEN"
    bydlan_anthropic_api_key = "ANTHROPIC_API_KEY"

async def get_value(key: Keys) -> str:
    """Get environment variable value with validation"""
    value = os.getenv(key.value)
    
    if value is None or value.strip() == "":
        print(f"ERROR: Environment variable {key.value} is not set!")
        print("Required environment variables:")
        for k in Keys:
            print(f"  - {k.value}")
        sys.exit(1)
    
    return value.strip()

def check_all_env_vars():
    """Check if all required environment variables are set"""
    missing = []
    for key in Keys:
        if not os.getenv(key.value):
            missing.append(key.value)
    
    if missing:
        print("ERROR: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set all required environment variables before starting the bot.")
        sys.exit(1)
