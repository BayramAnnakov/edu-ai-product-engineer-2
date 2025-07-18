import os
from pathlib import Path
from typing import Dict, Any


class AppConfig:
    """Application configuration constants and settings."""
    
    # Application metadata
    APP_TITLE = "📊 MBank Reviews Analysis Dashboard"
    APP_ICON = "📊"
    DEFAULT_APP_ID = "com.maanavan.mb_kyrgyzstan"
    
    # Dashboard settings
    DEFAULT_PORT = 8501
    DEFAULT_HOST = "localhost"
    
    # Review analysis settings
    DEFAULT_REVIEW_COUNT = 100
    MIN_REVIEW_COUNT = 10
    MAX_REVIEW_COUNT = 1000
    DEFAULT_LANGUAGE = "ru"
    DEFAULT_COUNTRY = "kg"
    
    # File paths
    RESULTS_DIR = "results"
    DEFAULT_REVIEWS_FILE = "results/mbank_reviews.json"
    DEFAULT_RESULTS_FILE = "results/summary_comparison_results.json"
    
    # Processing settings
    BATCH_SIZE = 200
    MAX_REVIEWS_LIMIT = 10000
    
    # UI settings
    LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"


class SummarizationConfig:
    """Configuration for summarization algorithms."""
    
    # Extractive summarization
    EXTRACTIVE_SENTENCE_COUNT = 3
    EXTRACTIVE_LANGUAGE = "russian"
    
    # GPT settings
    GPT_MODEL = "gpt-4"
    GPT_MAX_TOKENS = 500
    GPT_TEMPERATURE = 0.3
    
    # OpenAI Agents SDK settings
    AGENT_MODEL = "gpt-4"
    AGENT_TEMPERATURE = 0.3
    AGENT_MAX_TOKENS = 1000
    AGENT_TIMEOUT = 60  # seconds
    
    # Analysis prompts
    SUMMARIZATION_PROMPT = """
    Проанализируйте следующие отзывы о мобильном банковском приложении MBank и создайте краткое резюме основных моментов:

    {reviews_text}

    Пожалуйста, создайте краткое резюме (3-4 предложения), которое включает:
    1. Основные жалобы пользователей
    2. Положительные аспекты приложения
    3. Наиболее часто упоминаемые проблемы
    4. Общее впечатление пользователей

    Резюме должно быть на русском языке и быть информативным для разработчиков приложения.
    """
    
    EVALUATION_PROMPT = """
    Сравните два резюме отзывов о приложении MBank:

    Извлекающее резюме: {extractive_summary}
    Абстрактивное резюме: {abstractive_summary}

    Оцените их по следующим критериям и дайте рекомендацию:
    1. Полнота охвата информации
    2. Ясность и читаемость
    3. Практическая ценность для разработчиков
    4. Сохранение ключевых деталей

    Ответьте в формате JSON:
    {{
        "analysis": {{
            "extractive_coverage": "оценка 1-10",
            "abstractive_coverage": "оценка 1-10", 
            "extractive_clarity": "оценка 1-10",
            "abstractive_clarity": "оценка 1-10",
            "preferred_summary": "extractive/abstractive",
            "reasoning": "обоснование выбора"
        }}
    }}
    """


class UIConfig:
    """UI styling and layout configuration."""
    
    CUSTOM_CSS = """
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: rgb(14, 17, 23);;
            padding: 1rem;
            border-radius: 10px;
            border-left: 5px solid #1f77b4;
        }
        .summary-box {
            background-color: rgb(14, 17, 23);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin: 1rem 0;
        }
        .review-item {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 3px solid #28a745;
        }
    </style>
    """
    
    # Chart color schemes
    RATING_COLOR_SCALE = "RdYlGn"
    
    # Tab names
    TAB_NAMES = [
        "📊 Обзор", 
        "📝 Резюме", 
        "📱 Отзывы", 
        "📈 Аналитика", 
        "🚀 Новый анализ"
    ]


def get_env_var(var_name: str, default: Any = None) -> Any:
    """Get environment variable with optional default value."""
    return os.getenv(var_name, default)


def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def get_openai_config() -> Dict[str, Any]:
    """Get OpenAI configuration from environment."""
    load_env_file()
    return {
        "api_key": get_env_var("OPENAI_API_KEY"),
        "model": get_env_var("OPENAI_MODEL", SummarizationConfig.GPT_MODEL),
        "max_tokens": int(get_env_var("OPENAI_MAX_TOKENS", SummarizationConfig.GPT_MAX_TOKENS)),
        "temperature": float(get_env_var("OPENAI_TEMPERATURE", SummarizationConfig.GPT_TEMPERATURE))
    }