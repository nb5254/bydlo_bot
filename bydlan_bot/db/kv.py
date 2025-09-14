from enum import Enum
import os

class Keys(Enum):
    tg_client_api_id = "TG_API_ID"
    tg_client_api_hash = "TG_API_HASH"
    tg_bot_token_bydlan = "TG_BOT_TOKEN"
    bydlan_anthropic_api_key = "ANTHROPIC_API_KEY"

async def get_value(key: Keys) -> str:
    return os.getenv(key.value)