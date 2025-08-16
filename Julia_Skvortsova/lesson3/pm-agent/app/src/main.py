import asyncio
import os
import structlog
from langfuse import Langfuse
from datetime import datetime
from src.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def test_langfuse_connection():
    """Test Langfuse connection"""
    try:
        # Initialize Langfuse client
        langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://langfuse:3000"),
        )
        
        # Just test that we can create a client instance
        logger.info("Langfuse client initialized successfully", 
                   host=os.getenv("LANGFUSE_HOST"))
        
        return True
        
    except Exception as e:
        logger.exception("Failed to connect to Langfuse")
        return False

async def main():
    """Main entry point for the PM Agent application"""
    logger.info("Starting PM Agent application...")
    
    # Test database connection
    try:
        from src.db.base import engine
        async with engine.begin() as conn:
            # Just test the connection
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.exception("Database connection failed")
        # Don't exit - database might not be ready yet
    
    # Test Langfuse connection
    langfuse_ok = await test_langfuse_connection()
    if not langfuse_ok:
        logger.warning("Langfuse connection failed - observability may be limited")

    # TODO: main workflow starts here

    # For now, just keep the app running
    logger.info("PM Agent is ready and waiting for tasks...")
    
    # Keep the application running
    try:
        while True:
            await asyncio.sleep(60)
            logger.debug("PM Agent heartbeat", timestamp=datetime.now().isoformat())
    except KeyboardInterrupt:
        logger.info("Shutting down PM Agent...")

if __name__ == "__main__":
    asyncio.run(main())