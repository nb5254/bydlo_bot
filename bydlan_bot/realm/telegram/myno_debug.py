import structlog

logger = structlog.get_logger()

async def send_debug_message(msg: str):
    logger.info("Debug message", message=msg)