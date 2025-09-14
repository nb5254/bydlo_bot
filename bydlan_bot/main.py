import asyncio
import signal
import os
import structlog
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
    
    try:
        # Initialize Anthropic API
        await anthropic_api.init()
        logger.info("Anthropic API initialized")
        
        # Initialize Bydlan bot with FloodWait handling
        while True:
            try:
                await bydlan_init()
                logger.info("Bydlan bot initialized")
                break
            except FloodWait as e:
                logger.warning(f"FloodWait: waiting {e.value} seconds before retry")
                await asyncio.sleep(e.value)
                continue
        
        logger.info("Bot is running...")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error("Error in main", error=e)
    finally:
        try:
            await graceful_shutdown()
        except Exception as e:
            logger.error("Error during shutdown", error=e)

if __name__ == "__main__":
    asyncio.run(main())
