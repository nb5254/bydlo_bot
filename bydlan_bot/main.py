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
from db.kv import check_all_env_vars

# Configure logging - make it simpler for debugging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()  # Changed to Console for better readability
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def main():
    # Check environment variables first
    logger.info("Checking environment variables...")
    check_all_env_vars()
    logger.info("Environment variables validated")
    
    # Add random delay to avoid immediate rate limiting
    delay = random.randint(5, 15)  # Reduced delay for faster testing
    logger.info(f"Starting bot in {delay} seconds to avoid rate limits...")
    await asyncio.sleep(delay)
    
    try:
        # Initialize Anthropic API
        logger.info("Initializing Anthropic API...")
        await anthropic_api.init()
        logger.info("Anthropic API initialized successfully")
        
        # Initialize Bydlan bot with FloodWait handling
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Initializing Telegram bot (attempt {retry_count + 1}/{max_retries})...")
                await bydlan_init()
                logger.info("Bydlan bot initialized successfully!")
                break
                
            except FloodWait as e:
                retry_count += 1
                wait_time = min(e.value, 900)  # Cap at 15 minutes
                logger.warning(f"FloodWait: waiting {wait_time} seconds before retry (attempt {retry_count})")
                
                if retry_count >= max_retries:
                    logger.error("Max retries reached due to FloodWait. Bot will exit.")
                    return
                    
                await asyncio.sleep(wait_time)
                continue
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Bot initialization failed (attempt {retry_count})", error=str(e), exc_info=True)
                
                if retry_count >= max_retries:
                    logger.error("Max retries reached. Bot will exit.")
                    raise
                    
                wait_time = min(30 * retry_count, 180)  # Reduced wait time for testing
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
        
        # Check if client was initialized
        client = get_bydlan()
        if not client:
            logger.error("Bot client not initialized properly")
            return
        
        logger.info("=" * 50)
        logger.info("🎉 BOT IS RUNNING AND READY TO RESPOND! 🎉")
        logger.info("Add the bot to a group and type 'быдлан hello' to test")
        logger.info("=" * 50)
        
        # Use Pyrogram's idle() to keep the bot running
        await idle()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Critical error in main", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("Shutting down bot...")
        await graceful_shutdown()
        logger.info("Bot shutdown complete")

def run():
    """Run the bot with proper signal handling"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set up signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: loop.stop())
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        loop.close()

if __name__ == "__main__":
    run()
