"""Utility functions for the pipeline"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import logging
from openai import AsyncOpenAI
import asyncio
from functools import wraps


# Configure logging
def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    # Create handler that properly handles Unicode
    handler = logging.StreamHandler()
    handler.setLevel(level)
    
    # Set UTF-8 encoding
    if hasattr(handler.stream, 'reconfigure'):
        handler.stream.reconfigure(encoding='utf-8')
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    
    return logging.getLogger(__name__)


logger = setup_logging()


class ArtifactManager:
    """Manages artifact storage for pipeline runs"""
    
    def __init__(self, base_dir: str = "artifacts"):
        self.base_dir = Path(base_dir)
        self.run_dir: Optional[Path] = None
        
    def start_run(self) -> Path:
        """Create a new run directory with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.run_dir = self.base_dir / timestamp
        self.run_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created artifact directory: {self.run_dir}")
        return self.run_dir
    
    def save_json(self, data: Any, filename: str) -> Path:
        """Save data as JSON"""
        if not self.run_dir:
            raise RuntimeError("No active run directory. Call start_run() first.")
        
        filepath = self.run_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            if hasattr(data, 'model_dump'):
                json.dump(data.model_dump(), f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.debug(f"Saved {filename}")
        return filepath
    
    def save_text(self, content: str, filename: str) -> Path:
        """Save text content"""
        if not self.run_dir:
            raise RuntimeError("No active run directory. Call start_run() first.")
        
        filepath = self.run_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"Saved {filename}")
        return filepath
    
    def get_path(self, filename: str) -> Path:
        """Get full path for a file in current run"""
        if not self.run_dir:
            raise RuntimeError("No active run directory. Call start_run() first.")
        return self.run_dir / filename


class OpenAIManager:
    """Manages OpenAI API interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def complete(
        self,
        prompt: str,
        model: str = "gpt-4.1",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None
    ) -> str:
        """Get completion from OpenAI"""
        try:
            logger.debug(f"Calling {model} with prompt length: {len(prompt)}")
            
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


def log_step(step_name: str):
    """Decorator to log pipeline steps"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info(f"Starting: {step_name}")
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Completed: {step_name} (took {duration:.1f}s)")
                return result
            except Exception as e:
                logger.error(f"Failed: {step_name} - {e}")
                raise
        return wrapper
    return decorator


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split a list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def run_concurrent(tasks: list, max_concurrent: int = 5):
    """Run async tasks with concurrency limit"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_with_semaphore(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])


def format_percentage(value: float) -> str:
    """Format a float as percentage"""
    return f"{value:.1f}%"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."