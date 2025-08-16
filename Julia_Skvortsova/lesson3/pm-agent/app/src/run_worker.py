"""
Redis queue worker for approval execution

"""
import asyncio
import signal
import structlog
from arq import run_worker
from arq.worker import create_worker
from arq.connections import RedisSettings

from src.config import settings
from src.queues.tasks import execute_approval, startup, shutdown

# Configure logging to match main app
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

class WorkerSettings:
    """arq worker configuration"""
    
    # Worker functions
    functions = [execute_approval]
    
    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown
    
    # Redis connection
    redis_settings = RedisSettings.from_dsn(settings.services_config.queue.redis_url)
    
    # Worker configuration from YAML
    max_jobs = settings.services_config.queue.max_jobs_per_worker
    job_timeout = settings.services_config.queue.job_timeout_seconds
    
    # Queue names to process
    queue_names = [
        settings.services_config.queue.high_priority_queue,
        settings.services_config.queue.normal_queue,
        settings.services_config.queue.low_priority_queue
    ]
    
    # Retry configuration
    retry_jobs = True
    max_tries = settings.services_config.queue.max_retries
    retry_delay = settings.services_config.queue.retry_delay_seconds

def main():
    """Main worker entry point"""
    logger.info("Starting approval queue worker...")
    
    try:
        asyncio.run(run_worker(WorkerSettings))
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
    except Exception as e:
        logger.exception("Worker failed", error=str(e))
        raise

if __name__ == "__main__":
    main()