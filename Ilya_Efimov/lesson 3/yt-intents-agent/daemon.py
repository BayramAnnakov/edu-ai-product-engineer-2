import asyncio
import logging
from bot import run_bot
from scheduler import SchedulerManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_combined_daemon():
    """Запускает бота и планировщик одновременно"""
    logger.info("Starting combined daemon mode...")
    
    # Создаем задачи для бота и планировщика
    bot_task = asyncio.create_task(run_bot())
    scheduler_task = asyncio.create_task(SchedulerManager.run_continuous())
    
    try:
        # Запускаем обе задачи параллельно
        await asyncio.gather(bot_task, scheduler_task)
    except KeyboardInterrupt:
        logger.info("Shutting down daemon...")
        bot_task.cancel()
        scheduler_task.cancel()
        
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
            
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(run_combined_daemon())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")