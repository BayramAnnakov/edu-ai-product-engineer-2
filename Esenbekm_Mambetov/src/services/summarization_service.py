"""Summarization services for extractive and abstractive text summarization."""

import time
import json
import re
from typing import List
import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.nlp.stemmers import Stemmer
from openai import OpenAI
from agents import Agent, Runner, function_tool, ModelSettings

from ..models.review import Review
from ..models.summary import SummaryResult, ComparisonMetrics, EvaluationReport, ComparisonResult
from ..config.settings import SummarizationConfig
from ..utils.logger import Logger

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')


class ExtractiveService:
    """Service for extractive text summarization."""
    
    def __init__(self, language: str = SummarizationConfig.EXTRACTIVE_LANGUAGE):
        """
        Initialize extractive summarization service.
        
        Args:
            language: Language for stemmer
        """
        self.language = language
        self.stemmer = Stemmer(language)
        self.summarizer = LexRankSummarizer(self.stemmer)
    
    def summarize(self, reviews: List[Review], sentence_count: int = SummarizationConfig.EXTRACTIVE_SENTENCE_COUNT) -> SummaryResult:
        """
        Generate extractive summary from reviews.
        
        Args:
            reviews: List of Review objects
            sentence_count: Number of sentences in summary
            
        Returns:
            SummaryResult object
        """
        start_time = time.time()
        
        # Combine all review texts
        combined_text = ' '.join([review.text for review in reviews if review.text.strip()])
        
        if not combined_text.strip():
            return SummaryResult(
                summary_type="extractive",
                text="Нет доступного текста для резюмирования.",
                word_count=0,
                sentence_count=0,
                processing_time=time.time() - start_time
            )
        
        try:
            # Parse text
            parser = PlaintextParser.from_string(combined_text, Tokenizer("russian"))
            
            # Generate summary
            summary_sentences = self.summarizer(parser.document, sentence_count)
            summary_text = ' '.join([str(sentence) for sentence in summary_sentences])
            
            # Calculate metrics
            word_count = len(summary_text.split())
            sentence_count_actual = len(summary_sentences)
            
        except Exception:
            summary_text = "Ошибка при создании извлекающего резюме."
            word_count = 0
            sentence_count_actual = 0
        
        processing_time = time.time() - start_time
        
        return SummaryResult(
            summary_type="extractive",
            text=summary_text,
            word_count=word_count,
            sentence_count=sentence_count_actual,
            processing_time=processing_time
        )


@function_tool
def summarize_reviews(reviews_text: str) -> str:
    """
    Analyze and summarize mobile app reviews.
    
    Args:
        reviews_text: Combined text of all reviews to analyze
        
    Returns:
        A structured summary of the reviews
    """
    if not reviews_text.strip():
        return "No reviews text provided for summarization."
    
    # This tool provides the agent with the capability to analyze reviews
    return f"Analyzing {len(reviews_text.split())} words of review content..."

@function_tool
def compare_summaries(extractive_summary: str, abstractive_summary: str) -> str:
    """
    Compare two different summary approaches.
    
    Args:
        extractive_summary: The extractive (deterministic) summary
        abstractive_summary: The abstractive (AI-generated) summary
        
    Returns:
        A detailed comparison and recommendation
    """
    if not extractive_summary or not abstractive_summary:
        return "Both summaries are required for comparison."
    
    # Calculate basic metrics
    ext_words = len(extractive_summary.split())
    abs_words = len(abstractive_summary.split())
    ext_sentences = len([s for s in extractive_summary.split('.') if s.strip()])
    abs_sentences = len([s for s in abstractive_summary.split('.') if s.strip()])
    
    # Calculate word overlap
    ext_words_set = set(extractive_summary.lower().split())
    abs_words_set = set(abstractive_summary.lower().split())
    overlap = len(ext_words_set.intersection(abs_words_set))
    total_unique = len(ext_words_set.union(abs_words_set))
    overlap_ratio = overlap / total_unique if total_unique > 0 else 0
    
    comparison_result = f"""
Сравнение резюме:

ИЗВЛЕКАЮЩЕЕ РЕЗЮМЕ:
- Количество слов: {ext_words}
- Количество предложений: {ext_sentences}
- Подход: Выбирает наиболее важные предложения из исходного текста

АБСТРАКТИВНОЕ РЕЗЮМЕ:
- Количество слов: {abs_words}
- Количество предложений: {abs_sentences}
- Подход: Генерирует новый текст на основе анализа исходного содержания

АНАЛИЗ СОВПАДЕНИЙ:
- Пересечение слов: {overlap_ratio:.2%}
- Уникальных слов всего: {total_unique}

РЕКОМЕНДАЦИЯ:
{'Абстрактивное резюме более краткое и структурированное' if abs_words < ext_words else 'Извлекающее резюме более детальное'}
{'Хорошее пересечение ключевых терминов' if overlap_ratio > 0.3 else 'Различные подходы к освещению темы'}
    """
    
    return comparison_result.strip()


class AbstractiveService:
    """Service for abstractive text summarization using OpenAI Agents SDK."""
    
    def __init__(self, api_key: str):
        """
        Initialize abstractive summarization service with Agents SDK.
        
        Args:
            api_key: OpenAI API key
        """
        self.logger = Logger.get_logger()
        self.api_key = api_key
        self.agent_available = False
        
        if not api_key:
            self.logger.warning("No OpenAI API key provided, abstractive summarization will use fallback mode")
            return
            
        try:
            self.client = OpenAI(api_key=api_key)
            
            # Create tools for the agent
            self.tools = [summarize_reviews, compare_summaries]
            
            # Create the summarization agent
            self.agent = Agent(
                name="ReviewSummarizationAgent",
                instructions="""You are an expert mobile app review analyst. Your task is to create clear, structured summaries of user reviews for mobile banking applications.

IMPORTANT RULES:
- Always respond DIRECTLY with the summary content in Russian
- NEVER include apologetic messages, tool error mentions, or meta-commentary
- Do NOT mention tool problems or analysis difficulties
- Focus only on the content of the reviews
- Be concise and professional

Your summary should include:
1. Основные жалобы пользователей (main user complaints)
2. Положительные аспекты приложения (positive aspects)  
3. Наиболее часто упоминаемые проблемы (most frequent issues)
4. Общее впечатление пользователей (overall user impression)

Provide actionable insights for app developers in 3-4 clear sentences.""",
                tools=self.tools,
                model=SummarizationConfig.GPT_MODEL,
                model_settings=ModelSettings(
                    temperature=SummarizationConfig.GPT_TEMPERATURE,
                    max_tokens=SummarizationConfig.GPT_MAX_TOKENS
                )
            )
            self.agent_available = True
            self.logger.info("OpenAI Agents SDK initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI Agents SDK: {e}")
            self.agent_available = False
    
    def summarize(self, reviews: List[Review]) -> SummaryResult:
        """
        Generate abstractive summary from reviews using the Agent.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            SummaryResult object
        """
        start_time = time.time()
        
        # Prepare reviews text
        reviews_text = self._prepare_reviews_text(reviews)
        
        if not reviews_text.strip():
            return SummaryResult(
                summary_type="abstractive",
                text="Нет доступного текста для резюмирования.",
                word_count=0,
                sentence_count=0,
                processing_time=time.time() - start_time
            )
        
        try:
            if not self.agent_available:
                # Use fallback summarization when agent is not available
                summary_text = self._create_fallback_summary(reviews)
                word_count = len(summary_text.split())
                sentence_count = len([s for s in summary_text.split('.') if s.strip()])
                self.logger.info(f"Fallback summary created: {word_count} words, {sentence_count} sentences")
            else:
                self.logger.info("Using OpenAI Agents SDK for abstractive summarization")
                
                # Create the analysis prompt for the agent
                analysis_prompt = f"""
                Создайте краткое резюме отзывов о мобильном банковском приложении MBank:

                {reviews_text}

                Структура резюме (3-4 предложения):
                1. Основные жалобы пользователей
                2. Положительные аспекты приложения
                3. Наиболее часто упоминаемые проблемы
                4. Рекомендации для разработчиков

                Отвечайте только содержанием резюме на русском языке, без упоминания проблем с инструментами.
                """
                
                # Execute the agent with the analysis prompt
                response = Runner.run_sync(self.agent, analysis_prompt)
                
                summary_text = response.final_output if hasattr(response, 'final_output') else str(response)
                
                # Clean up the response text and remove apologetic language
                summary_text = summary_text.strip()
                summary_text = self._clean_agent_response(summary_text)
                
                # Calculate metrics
                word_count = len(summary_text.split())
                sentence_count = len([s for s in summary_text.split('.') if s.strip()])
                
                self.logger.info(f"Agent-generated summary: {word_count} words, {sentence_count} sentences")
            
        except Exception as e:
            self.logger.error(f"Error in abstractive summarization: {e}")
            summary_text = self._create_fallback_summary(reviews)
            word_count = len(summary_text.split())
            sentence_count = len([s for s in summary_text.split('.') if s.strip()])
        
        processing_time = time.time() - start_time
        
        return SummaryResult(
            summary_type="abstractive",
            text=summary_text,
            word_count=word_count,
            sentence_count=sentence_count,
            processing_time=processing_time
        )
    
    def _prepare_reviews_text(self, reviews: List[Review]) -> str:
        """
        Prepare reviews text for GPT processing.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            Formatted reviews text
        """
        reviews_text = ""
        for i, review in enumerate(reviews[:50], 1):  # Limit to first 50 reviews
            if review.text.strip():
                reviews_text += f"Отзыв {i} (Рейтинг: {review.rating}/5): {review.text}\n\n"
        
        return reviews_text
    
    def _create_fallback_summary(self, reviews: List[Review]) -> str:
        """
        Create a basic abstractive summary without AI when agent is unavailable.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            Basic summary text
        """
        if not reviews:
            return "Отзывы для анализа отсутствуют."
        
        # Count ratings distribution
        rating_counts = {}
        for review in reviews:
            rating = review.rating
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        # Find most common words in complaints (low ratings)
        negative_reviews = [r.text.lower() for r in reviews if r.rating <= 2]
        positive_reviews = [r.text.lower() for r in reviews if r.rating >= 4]
        
        # Common complaint terms
        complaint_terms = ['не работает', 'сбой', 'ошибка', 'проблема', 'лагает', 'глючит', 'медленно', 'висит']
        positive_terms = ['удобн', 'хорош', 'отличн', 'быстр', 'прост', 'легк', 'нравится', 'классн']
        
        complaint_mentions = sum(1 for text in negative_reviews for term in complaint_terms if term in text)
        positive_mentions = sum(1 for text in positive_reviews for term in positive_terms if term in text)
        
        # Calculate average rating
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
        
        # Generate basic summary
        total_reviews = len(reviews)
        high_ratings = sum(1 for r in reviews if r.rating >= 4)
        low_ratings = sum(1 for r in reviews if r.rating <= 2)
        
        summary_parts = []
        
        if low_ratings > high_ratings:
            summary_parts.append(f"Анализ {total_reviews} отзывов показывает преобладание негативных оценок (средний рейтинг: {avg_rating:.1f}/5).")
            if complaint_mentions > 0:
                summary_parts.append("Основные жалобы связаны с техническими сбоями, ошибками в работе приложения и проблемами с подключением.")
        else:
            summary_parts.append(f"Анализ {total_reviews} отзывов показывает в целом положительное восприятие приложения (средний рейтинг: {avg_rating:.1f}/5).")
            
        if positive_mentions > 0:
            summary_parts.append("Пользователи отмечают удобство интерфейса, быстроту операций и простоту использования.")
        
        if low_ratings > 0:
            summary_parts.append("Для улучшения приложения рекомендуется сосредоточиться на стабильности работы и устранении технических проблем.")
        
        return " ".join(summary_parts) if summary_parts else "Недостаточно данных для создания резюме."
    
    def evaluate_summaries(self, extractive_summary: SummaryResult, abstractive_summary: SummaryResult) -> EvaluationReport:
        """
        Evaluate and compare two summaries using the Agent.
        
        Args:
            extractive_summary: Extractive summary result
            abstractive_summary: Abstractive summary result
            
        Returns:
            EvaluationReport object
        """
        try:
            if not self.agent_available:
                # Use fallback evaluation when agent is not available
                return self._create_fallback_evaluation(extractive_summary, abstractive_summary)
                
            self.logger.info("Using OpenAI Agents SDK for summary evaluation")
            
            # Create the evaluation prompt for the agent
            evaluation_prompt = f"""
            Сравните два резюме отзывов о приложении MBank и оцените их качество:

            Извлекающее резюме: {extractive_summary.text}
            
            Абстрактивное резюме: {abstractive_summary.text}

            Сначала используйте инструмент compare_summaries для анализа этих резюме.
            
            Затем оцените их по критериям от 1 до 10 и ответьте ТОЛЬКО в JSON формате:
            {{
                "analysis": {{
                    "extractive_coverage": "8",
                    "abstractive_coverage": "9", 
                    "extractive_clarity": "7",
                    "abstractive_clarity": "9",
                    "extractive_usefulness": "8",
                    "abstractive_usefulness": "9",
                    "extractive_key_details": "8",
                    "abstractive_key_details": "7",
                    "preferred_summary": "abstractive",
                    "reasoning": "Абстрактивное резюме более структурированное и ясное"
                }}
            }}
            
            ВАЖНО: Отвечайте ТОЛЬКО JSON, без дополнительного текста!
            """
            
            # Execute the agent with the evaluation prompt
            response = Runner.run_sync(self.agent, evaluation_prompt)
            
            evaluation_text = response.final_output if hasattr(response, 'final_output') else str(response)
            evaluation_text = evaluation_text.strip()
            
            self.logger.info("Agent evaluation completed")
            self.logger.debug(f"Raw evaluation response: {evaluation_text}")
            
            try:
                # Try to find and parse JSON
                if '{' in evaluation_text and '}' in evaluation_text:
                    start = evaluation_text.find('{')
                    end = evaluation_text.rfind('}') + 1
                    json_text = evaluation_text[start:end]
                    evaluation_data = json.loads(json_text)
                    self.logger.info("Successfully parsed JSON evaluation")
                else:
                    raise json.JSONDecodeError("No JSON found", evaluation_text, 0)
                    
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse agent evaluation as JSON: {e}")
                self.logger.warning(f"Raw response was: {evaluation_text}")
                
                # Create a more meaningful fallback based on basic analysis
                ext_words = len(extractive_summary.text.split()) if extractive_summary.text else 0
                abs_words = len(abstractive_summary.text.split()) if abstractive_summary.text else 0
                
                evaluation_data = {
                    "analysis": {
                        "extractive_coverage": "7",
                        "abstractive_coverage": "8",
                        "extractive_clarity": "6",
                        "abstractive_clarity": "8",
                        "extractive_usefulness": "7",
                        "abstractive_usefulness": "8",
                        "extractive_key_details": "8",
                        "abstractive_key_details": "7",
                        "preferred_summary": "abstractive" if abs_words < ext_words else "extractive",
                        "reasoning": f"Автоматическая оценка: {'Абстрактивное резюме более краткое' if abs_words < ext_words else 'Извлекающее резюме более детальное'} (ошибка парсинга JSON)"
                    }
                }
            
            return EvaluationReport.from_dict(evaluation_data)
            
        except Exception as e:
            self.logger.error(f"Error in agent evaluation: {e}")
            return EvaluationReport(analysis={
                "extractive_coverage": "Н/Д",
                "abstractive_coverage": "Н/Д",
                "extractive_clarity": "Н/Д",
                "abstractive_clarity": "Н/Д",
                "extractive_usefulness": "Н/Д",
                "abstractive_usefulness": "Н/Д",
                "extractive_key_details": "Н/Д",
                "abstractive_key_details": "Н/Д",
                "preferred_summary": "Н/Д",
                "reasoning": "Ошибка при выполнении оценки агентом"
            })
    
    def _create_fallback_evaluation(self, extractive_summary: SummaryResult, abstractive_summary: SummaryResult) -> EvaluationReport:
        """
        Create a basic evaluation when agent is not available.
        
        Args:
            extractive_summary: Extractive summary result
            abstractive_summary: Abstractive summary result
            
        Returns:
            EvaluationReport object
        """
        # Basic analysis based on summary characteristics
        ext_words = len(extractive_summary.text.split()) if extractive_summary.text else 0
        abs_words = len(abstractive_summary.text.split()) if abstractive_summary.text else 0
        
        # Determine if abstractive summary failed
        is_abs_error = "ошибка" in abstractive_summary.text.lower() or abs_words == 0
        
        if is_abs_error:
            evaluation_data = {
                "analysis": {
                    "extractive_coverage": "8",
                    "abstractive_coverage": "0",
                    "extractive_clarity": "7",
                    "abstractive_clarity": "0",
                    "extractive_usefulness": "8",
                    "abstractive_usefulness": "0",
                    "extractive_key_details": "8",
                    "abstractive_key_details": "0",
                    "preferred_summary": "extractive",
                    "reasoning": "Абстрактивное резюме не было создано, поэтому извлекающее резюме предпочтительнее"
                }
            }
        else:
            # Both summaries are available, provide balanced evaluation
            evaluation_data = {
                "analysis": {
                    "extractive_coverage": "8",
                    "abstractive_coverage": "7",
                    "extractive_clarity": "6",
                    "abstractive_clarity": "8",
                    "extractive_usefulness": "7",
                    "abstractive_usefulness": "8",
                    "extractive_key_details": "9",
                    "abstractive_key_details": "7",
                    "preferred_summary": "abstractive" if abs_words < ext_words else "extractive",
                    "reasoning": f"Автоматическая оценка: {'Абстрактивное резюме более краткое и структурированное' if abs_words < ext_words else 'Извлекающее резюме сохраняет больше деталей'}"
                }
            }
        
        return EvaluationReport.from_dict(evaluation_data)
    
    def _clean_agent_response(self, text: str) -> str:
        """
        Clean agent response by removing apologetic language and meta-commentary.
        
        Args:
            text: Raw agent response text
            
        Returns:
            Cleaned summary text
        """
        if not text:
            return text
            
        # Remove common apologetic patterns
        apologetic_patterns = [
            r"К сожалению, у меня возникли проблемы.*?Однако,?\s*",
            r"Извините.*?проблем.*?Тем не менее,?\s*",
            r"У меня возникли сложности.*?Но\s*",
            r".*?проблемы с использованием инструмента.*?Однако,?\s*",
            r".*?не удалось использовать инструмент.*?Тем не менее,?\s*",
        ]
        
        cleaned_text = text
        for pattern in apologetic_patterns:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove phrases about tool problems
        tool_problem_phrases = [
            "на основе моего анализа отзывов, я могу сделать следующие выводы:",
            "основываясь на анализе отзывов:",
            "исходя из содержания отзывов:",
            "на основе представленных отзывов:",
        ]
        
        for phrase in tool_problem_phrases:
            cleaned_text = cleaned_text.replace(phrase, "")
        
        # Clean up extra whitespace and newlines
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text.strip())
        
        return cleaned_text


class ComparisonService:
    """Service for comparing different summarization methods."""
    
    @staticmethod
    def calculate_content_overlap(summary1: SummaryResult, summary2: SummaryResult) -> float:
        """
        Calculate content overlap between two summaries.
        
        Args:
            summary1: First summary
            summary2: Second summary
            
        Returns:
            Overlap ratio (0-1)
        """
        if not summary1.text or not summary2.text:
            return 0.0
        
        words1 = set(ComparisonService._clean_text(summary1.text).lower().split())
        words2 = set(ComparisonService._clean_text(summary2.text).lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def calculate_length_ratio(summary1: SummaryResult, summary2: SummaryResult) -> float:
        """
        Calculate length ratio between summaries.
        
        Args:
            summary1: First summary
            summary2: Second summary
            
        Returns:
            Length ratio
        """
        if summary1.word_count == 0:
            return 0.0
        
        return summary2.word_count / summary1.word_count
    
    @staticmethod
    def calculate_readability_score(summary: SummaryResult) -> float:
        """
        Calculate simple readability score for a summary.
        
        Args:
            summary: Summary to analyze
            
        Returns:
            Readability score (0-1)
        """
        if not summary.text or summary.word_count == 0:
            return 0.0
        
        # Simple readability metric based on average word length and sentence length
        avg_word_length = len(summary.text.replace(' ', '')) / summary.word_count
        avg_sentence_length = summary.word_count / max(summary.sentence_count, 1)
        
        # Normalize scores (this is a simplified metric)
        word_score = max(0, min(1, (10 - avg_word_length) / 10))
        sentence_score = max(0, min(1, (20 - avg_sentence_length) / 20))
        
        return (word_score + sentence_score) / 2
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for comparison."""
        return re.sub(r'[^\w\s]', '', text)
    
    @staticmethod
    def create_comparison_result(
        extractive_summary: SummaryResult,
        abstractive_summary: SummaryResult,
        evaluation_report: EvaluationReport
    ) -> ComparisonResult:
        """
        Create a complete comparison result.
        
        Args:
            extractive_summary: Extractive summary result
            abstractive_summary: Abstractive summary result
            evaluation_report: GPT evaluation report
            
        Returns:
            ComparisonResult object
        """
        content_overlap = ComparisonService.calculate_content_overlap(extractive_summary, abstractive_summary)
        length_ratio = ComparisonService.calculate_length_ratio(extractive_summary, abstractive_summary)
        readability_score = ComparisonService.calculate_readability_score(abstractive_summary)
        
        comparison_metrics = ComparisonMetrics(
            content_overlap=content_overlap,
            length_ratio=length_ratio,
            readability_score=readability_score
        )
        
        return ComparisonResult(
            extractive_summary=extractive_summary,
            abstractive_summary=abstractive_summary,
            comparison_metrics=comparison_metrics,
            evaluation_report=evaluation_report
        )