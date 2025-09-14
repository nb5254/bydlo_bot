import asyncio
import signal
import os
import structlog
import random
from realm.anthropic import api as anthropic_api
from bydlan import init as bydlan_init, graceful_shutdown
from pyrogram.errors import FloodWait

# Configure logging
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

async def main():
    logger = structlog.get_logger()
    
    # Add random delay to avoid immediate rate limiting
    delay = random.randint(10, 30)
    logger.info(f"Starting bot in {delay} seconds to avoid rate limits...")
    await asyncio.sleep(delay)
    
    try:
        # Initialize Anthropic API
        logger.info("Initializing Anthropic API...")
        await anthropic_api.init()
        logger.info("Anthropic API initialized")
        
        # Initialize Bydlan bot with FloodWait handling
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Initializing bot (attempt {retry_count + 1}/{max_retries})...")
                await bydlan_init()
                logger.info("Bydlan bot initialized successfully!")
                break
                
            except FloodWait as e:
                retry_count += 1
                wait_time = min(e.value, 900)  # Cap at 15 minutes
                logger.warning(f"FloodWait: waiting {wait_time} seconds before retry (attempt {retry_count})")
                
                if retry_count >= max_retries:
                    logger.error("Max retries reached. Bot will exit.")
                    return
                    
                await asyncio.sleep(wait_time)
                continue
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Bot initialization failed (attempt {retry_count}): {e}")
                
                if retry_count >= max_retries:
                    logger.error("Max retries reached. Bot will exit.")
                    raise
                    
                wait_time = min(60 * retry_count, 300)  # Exponential backoff, cap at 5 minutes
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
        
        logger.info("🎉 Bot is running and ready to respond!")
        logger.info("Add the bot to a group and type 'быдлан hello' to test")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error("Critical error in main", error=e)
        raise
    finally:
        try:
            logger.info("Shutting down bot...")
            await graceful_shutdown()
            logger.info("Bot shutdown complete")
        except Exception as e:
            logger.error("Error during shutdown", error=e)

if __name__ == "__main__":
    asyncio.run(main())
