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
        print(f"❌ ERROR: Environment variable {key.value} is not set!")
        print("\n📝 Required environment variables:")
        print("  - TG_API_ID: Your Telegram API ID (get from https://my.telegram.org)")
        print("  - TG_API_HASH: Your Telegram API Hash")
        print("  - TG_BOT_TOKEN: Your bot token from @BotFather")
        print("  - ANTHROPIC_API_KEY: Your Anthropic/Claude API key")
        print("\n⚠️  Set these in Railway's Variables section!")
        sys.exit(1)
    
    return value.strip()

def check_all_env_vars():
    """Check if all required environment variables are set"""
    missing = []
    for key in Keys:
        if not os.getenv(key.value):
            missing.append(key.value)
    
    if missing:
        print("❌ ERROR: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\n📝 Set these in Railway's Variables section:")
        print("  1. Go to your Railway project")
        print("  2. Click on your deployment")
        print("  3. Go to 'Variables' tab")
        print("  4. Add each variable with its value")
        sys.exit(1)
