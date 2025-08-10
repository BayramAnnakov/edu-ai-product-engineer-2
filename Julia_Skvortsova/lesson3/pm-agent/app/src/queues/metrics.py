"""Queue metrics collection"""
import time
from typing import Dict, List
from datetime import datetime
import structlog

logger = structlog.get_logger()

class QueueMetrics:
    """Simple in-memory metrics collector for queue operations"""
    
    def __init__(self):
        self.execution_times: List[float] = []
        self.success_count = 0
        self.failure_count = 0
        self.timeout_count = 0
        self.start_time = time.time()
        
    async def record_success(self, execution_time: float):
        """Record successful execution"""
        self.execution_times.append(execution_time)
        self.success_count += 1
        
        logger.debug(
            "Approval execution success",
            execution_time=execution_time,
            total_successes=self.success_count
        )
        
    async def record_failure(self, error: str):
        """Record failed execution"""
        self.failure_count += 1
        
        logger.warning(
            "Approval execution failure",
            error=error,
            total_failures=self.failure_count
        )
        
    async def record_timeout(self):
        """Record timeout"""
        self.timeout_count += 1
        
        logger.warning(
            "Approval execution timeout",
            total_timeouts=self.timeout_count
        )
        
    def get_stats(self) -> Dict[str, any]:
        """Get current metrics"""
        total_executions = self.success_count + self.failure_count
        uptime = time.time() - self.start_time
        
        if self.execution_times:
            avg_execution_time = sum(self.execution_times) / len(self.execution_times)
            max_execution_time = max(self.execution_times)
            min_execution_time = min(self.execution_times)
        else:
            avg_execution_time = max_execution_time = min_execution_time = 0
            
        return {
            "total_executions": total_executions,
            "successes": self.success_count,
            "failures": self.failure_count,
            "timeouts": self.timeout_count,
            "success_rate": self.success_count / total_executions if total_executions > 0 else 0,
            "avg_execution_time_seconds": avg_execution_time,
            "min_execution_time_seconds": min_execution_time,
            "max_execution_time_seconds": max_execution_time,
            "uptime_seconds": uptime
        }

# Global metrics instance
queue_metrics = QueueMetrics()