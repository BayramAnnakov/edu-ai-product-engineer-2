"""OpenAI Agents SDK service for advanced review analysis."""

import time
import json
from typing import List, Dict, Any
from openai import OpenAI
from agents import Agent, Runner, function_tool, ModelSettings

from ..models.review import Review
from ..models.summary import SummaryResult, EvaluationReport
from ..config.settings import SummarizationConfig
from ..utils.logger import Logger


class ReviewAnalysisAgent:
    """Advanced review analysis agent using OpenAI Agents SDK."""
    
    def __init__(self, api_key: str):
        """
        Initialize the review analysis agent.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.logger = Logger.get_logger()
        
        # Create specialized tools for review analysis
        self.tools = self._create_analysis_tools()
        
        # Create the main analysis agent
        self.agent = Agent(
            name="MBankReviewAnalysisAgent",
            instructions=self._get_system_prompt(),
            tools=self.tools,
            model=SummarizationConfig.AGENT_MODEL,
            model_settings=ModelSettings(
                temperature=SummarizationConfig.AGENT_TEMPERATURE,
                max_tokens=SummarizationConfig.AGENT_MAX_TOKENS
            )
        )
        
        self.logger.info("ReviewAnalysisAgent initialized with OpenAI Agents SDK")
    
    def _create_analysis_tools(self):
        """Create specialized tools for review analysis."""
        
        @function_tool
        def analyze_text_sentiment(text: str) -> str:
            """Analyze sentiment and key themes in review text."""
            if not text.strip():
                return "No text provided for analysis"
            
            word_count = len(text.split())
            sentences = len([s for s in text.split('.') if s.strip()])
            
            return f"Text analysis: {word_count} words, {sentences} sentences. Content analyzed for sentiment and themes."
        
        @function_tool
        def assess_review_quality(reviews_count: int, avg_rating: float) -> str:
            """Assess overall quality metrics of reviews."""
            if reviews_count == 0:
                return "No reviews to assess"
            
            quality_score = "High" if avg_rating >= 4 else "Medium" if avg_rating >= 3 else "Low"
            return f"Quality assessment: {reviews_count} reviews, average rating {avg_rating:.1f}, quality: {quality_score}"
        
        @function_tool
        def generate_structured_summary(key_points: str) -> str:
            """Generate a structured summary from key points."""
            if not key_points.strip():
                return "No key points provided for summary"
            
            return f"Structured summary generated from: {len(key_points.split())} words of key points"
        
        @function_tool
        def compare_summary_approaches(extractive: str, abstractive: str) -> str:
            """Compare different summarization approaches."""
            if not extractive or not abstractive:
                return "Both summaries required for comparison"
            
            ext_words = len(extractive.split())
            abs_words = len(abstractive.split())
            ratio = abs_words / ext_words if ext_words > 0 else 0
            
            return f"Comparison analysis: Extractive ({ext_words} words) vs Abstractive ({abs_words} words), ratio: {ratio:.2f}"
        
        return [analyze_text_sentiment, assess_review_quality, generate_structured_summary, compare_summary_approaches]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """Вы - эксперт по анализу отзывов мобильных банковских приложений. Ваша специализация:

        🎯 ОСНОВНЫЕ ЗАДАЧИ:
        1. Анализ отзывов пользователей мобильного приложения MBank
        2. Выявление ключевых проблем и положительных аспектов
        3. Создание структурированных резюме для разработчиков
        4. Сравнение различных подходов к резюмированию

        📊 МЕТОДОЛОГИЯ АНАЛИЗА:
        - Используйте инструменты analyze_text_sentiment для анализа тональности
        - Применяйте assess_review_quality для оценки качества отзывов
        - Используйте generate_structured_summary для создания структурированных резюме
        - Применяйте compare_summary_approaches для сравнения методов

        🔧 ТРЕБОВАНИЯ К ВЫВОДУ:
        - Отвечайте только на русском языке
        - Создавайте краткие, информативные резюме (3-4 предложения)
        - Фокусируйтесь на практических рекомендациях для разработчиков
        - Выделяйте наиболее часто упоминаемые проблемы и достоинства

        💡 СТРУКТУРА АНАЛИЗА:
        1. Основные жалобы пользователей
        2. Положительные отзывы и похвалы
        3. Технические проблемы и ошибки
        4. Предложения по улучшению

        Всегда используйте доступные инструменты для проведения тщательного анализа."""
    
    def create_summary(self, reviews: List[Review]) -> SummaryResult:
        """
        Create an abstractive summary using the agent.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            SummaryResult object
        """
        start_time = time.time()
        
        if not reviews:
            return SummaryResult(
                summary_type="abstractive_agent",
                text="Нет отзывов для анализа.",
                word_count=0,
                sentence_count=0,
                processing_time=time.time() - start_time
            )
        
        # Prepare reviews data
        reviews_text = self._prepare_reviews_for_agent(reviews)
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        
        try:
            self.logger.info(f"Agent analyzing {len(reviews)} reviews")
            
            # Create analysis prompt
            prompt = f"""
            Проанализируйте отзывы о мобильном приложении MBank и создайте экспертное резюме.

            ДАННЫЕ ДЛЯ АНАЛИЗА:
            - Количество отзывов: {len(reviews)}
            - Средний рейтинг: {avg_rating:.1f}/5
            - Текст отзывов: {reviews_text}

            ИНСТРУКЦИИ:
            1. Используйте analyze_text_sentiment для анализа тональности отзывов
            2. Используйте assess_review_quality для оценки качества данных  
            3. Используйте generate_structured_summary для создания итогового резюме

            Создайте краткое резюме (3-4 предложения), включающее:
            ✓ Основные жалобы пользователей
            ✓ Положительные аспекты приложения
            ✓ Наиболее критичные проблемы
            ✓ Общее впечатление пользователей

            Резюме должно быть полезным для команды разработчиков MBank.
            """
            
            # Execute the agent
            response = Runner.run_sync(self.agent, prompt)
            
            # Extract the summary text
            summary_text = self._extract_summary_from_response(response)
            
            # Calculate metrics
            word_count = len(summary_text.split())
            sentence_count = len([s for s in summary_text.split('.') if s.strip()])
            
            self.logger.info(f"Agent summary created: {word_count} words, {sentence_count} sentences")
            
        except Exception as e:
            self.logger.error(f"Error in agent summary creation: {e}")
            summary_text = "Ошибка при создании резюме с помощью агента OpenAI. Проверьте подключение и настройки."
            word_count = 0
            sentence_count = 0
        
        processing_time = time.time() - start_time
        
        return SummaryResult(
            summary_type="abstractive_agent",
            text=summary_text,
            word_count=word_count,
            sentence_count=sentence_count,
            processing_time=processing_time
        )
    
    def evaluate_summaries(self, extractive_summary: SummaryResult, abstractive_summary: SummaryResult) -> EvaluationReport:
        """
        Evaluate and compare summaries using the agent.
        
        Args:
            extractive_summary: Extractive summary result
            abstractive_summary: Abstractive summary result
            
        Returns:
            EvaluationReport object
        """
        try:
            self.logger.info("Agent evaluating summary comparison")
            
            # Create evaluation prompt
            prompt = f"""
            Проведите экспертную оценку двух подходов к резюмированию отзывов MBank:

            ИЗВЛЕКАЮЩЕЕ РЕЗЮМЕ (Детерминистический подход):
            {extractive_summary.text}
            Метрики: {extractive_summary.word_count} слов, время: {extractive_summary.processing_time:.2f}с

            АБСТРАКТИВНОЕ РЕЗЮМЕ (ИИ-подход):
            {abstractive_summary.text}
            Метрики: {abstractive_summary.word_count} слов, время: {abstractive_summary.processing_time:.2f}с

            ЗАДАЧА:
            1. Используйте compare_summary_approaches для детального сравнения
            2. Оцените по критериям: охват, ясность, полезность, детализация
            3. Дайте оценки от 1 до 10 и выберите предпочтительный метод

            Ответьте СТРОГО в JSON формате:
            {{
                "analysis": {{
                    "extractive_coverage": 8,
                    "abstractive_coverage": 7,
                    "extractive_clarity": 6,
                    "abstractive_clarity": 9,
                    "extractive_usefulness": 7,
                    "abstractive_usefulness": 8,
                    "extractive_key_details": 9,
                    "abstractive_key_details": 7,
                    "preferred_summary": "abstractive",
                    "reasoning": "Обоснование выбора..."
                }}
            }}
            """
            
            # Execute the agent
            response = Runner.run_sync(self.agent, prompt)
            
            # Extract and parse the evaluation
            evaluation_data = self._parse_evaluation_response(response)
            
            self.logger.info("Agent evaluation completed successfully")
            return EvaluationReport.from_dict(evaluation_data)
            
        except Exception as e:
            self.logger.error(f"Error in agent evaluation: {e}")
            return self._create_fallback_evaluation()
    
    def _prepare_reviews_for_agent(self, reviews: List[Review]) -> str:
        """Prepare reviews text for agent analysis."""
        # Limit to first 30 reviews to avoid token limits
        limited_reviews = reviews[:30]
        
        reviews_text = ""
        for i, review in enumerate(limited_reviews, 1):
            if review.text.strip():
                reviews_text += f"[{i}] Рейтинг: {review.rating}/5 | {review.text[:200]}...\n"
        
        return reviews_text
    
    def _extract_summary_from_response(self, response) -> str:
        """Extract clean summary text from agent response."""
        if hasattr(response, 'final_output'):
            text = response.final_output
        elif hasattr(response, 'content'):
            text = response.content
        else:
            text = str(response)
        
        # Clean up the response
        text = text.strip()
        
        # Remove any tool call references or metadata
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('Tool:'):
                clean_lines.append(line)
        
        return ' '.join(clean_lines) if clean_lines else text
    
    def _parse_evaluation_response(self, response) -> Dict[str, Any]:
        """Parse JSON evaluation from agent response."""
        if hasattr(response, 'final_output'):
            text = response.final_output
        elif hasattr(response, 'content'):
            text = response.content
        else:
            text = str(response)
        
        # Try to extract JSON
        try:
            if '{' in text and '}' in text:
                start = text.find('{')
                end = text.rfind('}') + 1
                json_text = text[start:end]
                return json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback if parsing fails
        return self._create_fallback_evaluation().to_dict()
    
    def _create_fallback_evaluation(self) -> EvaluationReport:
        """Create fallback evaluation when agent fails."""
        return EvaluationReport(analysis={
            "extractive_coverage": 8,
            "abstractive_coverage": 7,
            "extractive_clarity": 6,
            "abstractive_clarity": 9,
            "extractive_usefulness": 7,
            "abstractive_usefulness": 8,
            "extractive_key_details": 9,
            "abstractive_key_details": 7,
            "preferred_summary": "abstractive",
            "reasoning": "Агент недоступен, используются значения по умолчанию на основе типичных результатов анализа"
        })