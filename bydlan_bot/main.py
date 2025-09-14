import asyncio
import signal
import os
import sys
import structlog
import random
from pyrogram import idle
from realm.anthropic import api as anthropic_api
from bydlan import init as bydlan_init, graceful_shutdown, get_bydlan
from pyrogram.errors import FloodWait

# Configure logging - simpler for Railway
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Check environment variables
def check_env_vars():
    """Check if all required environment variables are set"""
    required = ["TG_API_ID", "TG_API_HASH", "TG_BOT_TOKEN", "ANTHROPIC_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        logger.error(f"❌ Missing environment variables: {missing}")
        logger.info("Set these in Railway's Variables section!")
        sys.exit(1)
    
    logger.info("✅ All environment variables present")

async def main():
    logger.info("=" * 50)
    logger.info("STARTING BYDLAN BOT")
    logger.info("=" * 50)
    
    # Check environment variables
    check_env_vars()
    
    # Small delay to avoid rate limits
    delay = random.randint(3, 10)
    logger.info(f"Waiting {delay} seconds before connecting...")
    await asyncio.sleep(delay)
    
    try:
        # Initialize Anthropic API
        logger.info("Connecting to Anthropic API...")
        await anthropic_api.init()
        logger.info("✅ Anthropic API connected")
        
        # Initialize Telegram bot
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                logger.info(f"Connecting to Telegram (attempt {retry_count + 1}/{max_retries})...")
                await bydlan_init()
                logger.info("✅ Telegram bot connected")
                break
                
            except FloodWait as e:
                retry_count += 1
                wait_time = min(e.value, 300)
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                
                if retry_count >= max_retries:
                    logger.error("Too many rate limit errors. Exiting.")
                    return 1
                    
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Connection failed: {e}")
                
                if retry_count >= max_retries:
                    logger.error("Could not connect to Telegram after 3 attempts")
                    return 1
                
                wait_time = 30 * retry_count
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        # Check if bot is ready
        client = get_bydlan()
        if not client:
            logger.error("Bot client not initialized")
            return 1
        
        logger.info("=" * 50)
        logger.info("🎉 BOT IS RUNNING! 🎉")
        logger.info("Add bot to a Telegram group")
        logger.info("Make bot admin in the group")
        logger.info("Type: быдлан привет")
        logger.info("=" * 50)
        
        # Keep the bot running
        await idle()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    finally:
        logger.info("Shutting down...")
        await graceful_shutdown()
        logger.info("Shutdown complete")
        return 0

if __name__ == "__main__":
    # Simple runner for Railway
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to run bot: {e}")
        sys.exit(1)
