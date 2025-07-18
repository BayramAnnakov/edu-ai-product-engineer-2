"""UI components for the Streamlit dashboard."""

import streamlit as st
import pandas as pd
from typing import Optional

from ..models.review import ReviewsData
from ..models.summary import ComparisonResult
from ..config.settings import UIConfig


class UIComponents:
    """Reusable UI components for the dashboard."""
    
    @staticmethod
    def render_page_header():
        """Render the main page header."""
        st.markdown(UIConfig.CUSTOM_CSS, unsafe_allow_html=True)
        st.markdown(
            '<h1 class="main-header">📊 MBank Reviews Analysis Dashboard</h1>', 
            unsafe_allow_html=True
        )
    
    
    @staticmethod
    def render_summary_comparison(results: Optional[ComparisonResult]):
        """
        Render summary comparison section.
        
        Args:
            results: ComparisonResult object or None
        """
        if not results:
            st.warning("Нет данных для отображения сравнения резюме.")
            return
        
        st.header("📝 Сравнение резюме")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Извлекающее резюме (Deterministic)")
            extractive = results.extractive_summary
            st.markdown(f"""
            <div class="summary-box">
                <p><strong>Текст:</strong> {extractive.text}</p>
                <p><strong>Слов:</strong> {extractive.word_count}</p>
                <p><strong>Предложений:</strong> {extractive.sentence_count}</p>
                <p><strong>Время обработки:</strong> {extractive.processing_time:.2f}с</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("🤖 Абстрактивное резюме (GPT-4)")
            abstractive = results.abstractive_summary
            st.markdown(f"""
            <div class="summary-box">
                <p><strong>Текст:</strong> {abstractive.text}</p>
                <p><strong>Слов:</strong> {abstractive.word_count}</p>
                <p><strong>Предложений:</strong> {abstractive.sentence_count}</p>
                <p><strong>Время обработки:</strong> {abstractive.processing_time:.2f}с</p>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_metrics_dashboard(results: Optional[ComparisonResult]):
        """
        Render metrics dashboard.
        
        Args:
            results: ComparisonResult object or None
        """
        if not results or not results.comparison_metrics:
            st.warning("Нет данных метрик для отображения.")
            return
        
        st.header("📊 Метрики сравнения")
        
        metrics = results.comparison_metrics
        evaluation = results.evaluation_report
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Пересечение контента",
                value=f"{metrics.content_overlap:.3f}",
                help="Доля общих слов между резюме"
            )
        
        with col2:
            st.metric(
                label="Соотношение длины",
                value=f"{metrics.length_ratio:.3f}",
                help="Отношение длины абстрактивного к извлекающему"
            )
        
        with col3:
            st.metric(
                label="Оценка читаемости",
                value=f"{metrics.readability_score:.3f}",
                help="Оценка читаемости абстрактивного резюме"
            )
        
        with col4:
            preferred = evaluation.get_preferred_summary() if evaluation else 'Н/Д'
            st.metric(
                label="Предпочтительное резюме",
                value=preferred.title() if preferred and preferred != 'Н/Д' else 'Н/Д',
                help="Рекомендуемый тип резюме"
            )
    
    @staticmethod
    def render_reviews_table(reviews_data: Optional[ReviewsData]):
        """
        Render reviews table with filters.
        
        Args:
            reviews_data: ReviewsData object or None
        """
        if not reviews_data or not reviews_data.reviews:
            st.warning("Нет данных отзывов для отображения.")
            return
        
        st.header("📱 Отзывы пользователей")
        
        # Convert to DataFrame
        df = pd.DataFrame([review.to_dict() for review in reviews_data.reviews])
        
        # Add filters
        col1, col2 = st.columns(2)
        
        with col1:
            rating_filter = st.multiselect(
                "Фильтр по рейтингу:",
                options=sorted(df['rating'].unique()),
                default=sorted(df['rating'].unique())
            )
        
        with col2:
            search_text = st.text_input("Поиск в тексте отзывов:")
        
        # Apply filters
        filtered_df = df[df['rating'].isin(rating_filter)]
        
        if search_text:
            filtered_df = filtered_df[
                filtered_df['text'].str.contains(search_text, case=False, na=False)
            ]
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего отзывов", len(df))
        with col2:
            st.metric("Отфильтровано", len(filtered_df))
        with col3:
            avg_rating = filtered_df['rating'].mean() if len(filtered_df) > 0 else 0
            st.metric("Средний рейтинг", f"{avg_rating:.1f}")
        
        # Display table
        st.dataframe(
            filtered_df[['rating', 'author', 'date', 'text']],
            use_container_width=True,
            hide_index=True
        )
    
    @staticmethod
    def render_project_overview(reviews_data: Optional[ReviewsData], results: Optional[ComparisonResult]):
        """
        Render enhanced project overview section with comprehensive insights.
        
        Args:
            reviews_data: ReviewsData object or None
            results: ComparisonResult object or None
        """
        st.header("📊 Обзор анализа MBank Reviews")
        
        if not reviews_data or not reviews_data.reviews:
            st.warning("Нет данных для отображения обзора.")
            return
        
        # Key Statistics Section
        st.subheader("📈 Ключевые показатели")
        
        reviews = reviews_data.reviews
        total_reviews = len(reviews)
        avg_rating = sum(r.rating for r in reviews) / total_reviews if reviews else 0
        
        # Rating distribution
        rating_counts = {}
        for r in reviews:
            rating_counts[r.rating] = rating_counts.get(r.rating, 0) + 1
        
        positive_reviews = sum(rating_counts.get(i, 0) for i in [4, 5])
        negative_reviews = sum(rating_counts.get(i, 0) for i in [1, 2])
        neutral_reviews = rating_counts.get(3, 0)
        
        # Display key metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="📊 Всего отзывов",
                value=f"{total_reviews:,}",
                help="Общее количество проанализированных отзывов"
            )
        
        with col2:
            st.metric(
                label="⭐ Средний рейтинг",
                value=f"{avg_rating:.1f}/5",
                delta=f"{avg_rating - 3:.1f}" if avg_rating != 3 else None,
                help="Средняя оценка приложения"
            )
        
        with col3:
            positive_pct = (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0
            st.metric(
                label="👍 Положительные",
                value=f"{positive_reviews:,} ({positive_pct:.1f}%)",
                help="Отзывы с рейтингом 4-5 звезд"
            )
        
        with col4:
            negative_pct = (negative_reviews / total_reviews * 100) if total_reviews > 0 else 0
            st.metric(
                label="👎 Отрицательные", 
                value=f"{negative_reviews:,} ({negative_pct:.1f}%)",
                help="Отзывы с рейтингом 1-2 звезды"
            )
        
        with col5:
            neutral_pct = (neutral_reviews / total_reviews * 100) if total_reviews > 0 else 0
            st.metric(
                label="😐 Нейтральные",
                value=f"{neutral_reviews:,} ({neutral_pct:.1f}%)",
                help="Отзывы с рейтингом 3 звезды"
            )
        
        st.markdown("---")
        
        # App Information Section
        st.subheader("📱 Информация о приложении")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if reviews_data.metadata:
                metadata = reviews_data.metadata
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📋 Детали сбора данных</h4>
                    <p><strong>🏦 Приложение:</strong> {metadata.app_id}</p>
                    <p><strong>🌍 Регион:</strong> {metadata.country.upper()}</p>
                    <p><strong>🗣️ Язык:</strong> {metadata.language}</p>
                    <p><strong>📅 Дата анализа:</strong> {metadata.scraped_at[:19].replace('T', ' ')}</p>
                    <p><strong>⏱️ Период:</strong> Последние отзывы</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Analysis insights
            sentiment_emoji = "😊" if avg_rating >= 4 else "😐" if avg_rating >= 3 else "😞"
            trend_analysis = "положительная" if positive_reviews > negative_reviews else "отрицательная" if negative_reviews > positive_reviews else "нейтральная"
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>🔍 Быстрая аналитика</h4>
                <p><strong>🎯 Общее настроение:</strong> {sentiment_emoji} {trend_analysis.title()}</p>
                <p><strong>📊 Распределение:</strong> {positive_pct:.0f}% позитивных, {negative_pct:.0f}% негативных</p>
                <p><strong>🔥 Самый частый рейтинг:</strong> {max(rating_counts.items(), key=lambda x: x[1])[0]}⭐</p>
                <p><strong>📈 Качество данных:</strong> Высокое ({total_reviews} отзывов)</p>
                <p><strong>⚡ Актуальность:</strong> Свежие данные</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Summary Analysis Section
        if results:
            st.subheader("🤖 Результаты ИИ-анализа")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔍 Краткое резюме (Извлекающий метод)**")
                extractive = results.extractive_summary
                # Show first 200 characters of extractive summary
                preview_text = extractive.text[:200] + "..." if len(extractive.text) > 200 else extractive.text
                st.markdown(f"""
                <div class="summary-box">
                    <p>{preview_text}</p>
                    <small>📊 {extractive.word_count} слов • ⏱️ {extractive.processing_time:.2f}с</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**🤖 ИИ-анализ (Абстрактивный метод)**")
                abstractive = results.abstractive_summary
                # Show first 200 characters of abstractive summary  
                preview_text = abstractive.text[:200] + "..." if len(abstractive.text) > 200 else abstractive.text
                st.markdown(f"""
                <div class="summary-box">
                    <p>{preview_text}</p>
                    <small>📊 {abstractive.word_count} слов • ⏱️ {abstractive.processing_time:.2f}с</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Comparison metrics
            if results.comparison_metrics:
                st.markdown("**📊 Сравнительные метрики**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                metrics = results.comparison_metrics
                evaluation = results.evaluation_report
                
                with col1:
                    overlap_pct = metrics.content_overlap * 100
                    st.metric(
                        "🔗 Пересечение контента",
                        f"{overlap_pct:.1f}%",
                        help="Схожесть между двумя типами резюме"
                    )
                
                with col2:
                    st.metric(
                        "📏 Соотношение длины",
                        f"{metrics.length_ratio:.2f}",
                        help="Отношение длины ИИ-резюме к извлекающему"
                    )
                
                with col3:
                    readability_pct = metrics.readability_score * 100
                    st.metric(
                        "📚 Читаемость",
                        f"{readability_pct:.0f}%",
                        help="Оценка читаемости ИИ-резюме"
                    )
                
                with col4:
                    preferred = evaluation.get_preferred_summary() if evaluation else 'Н/Д'
                    emoji = "🤖" if preferred == "abstractive" else "🔍" if preferred == "extractive" else "❓"
                    st.metric(
                        "🏆 Рекомендация",
                        f"{emoji} {preferred.title() if preferred != 'Н/Д' else 'Н/Д'}",
                        help="Лучший тип резюме по оценке ИИ"
                    )
        
        else:
            st.info("🔄 Анализ резюме не выполнен. Запустите полный анализ для получения ИИ-инсайтов.")
        
        st.markdown("---")
        
        # Action Recommendations
        st.subheader("💡 Рекомендации")
        
        recommendations = []
        
        if negative_pct > 50:
            recommendations.append("🚨 **Критично:** Более половины отзывов негативные. Требуется срочное улучшение приложения.")
        elif negative_pct > 30:
            recommendations.append("⚠️ **Внимание:** Высокий процент негативных отзывов. Рекомендуется анализ основных проблем.")
        
        if avg_rating < 3:
            recommendations.append("📉 **Низкий рейтинг:** Средняя оценка ниже 3 звезд. Необходимы кардинальные улучшения.")
        elif avg_rating < 4:
            recommendations.append("📈 **Улучшение:** Есть потенциал для повышения рейтинга до 4+ звезд.")
        
        if positive_pct > 60:
            recommendations.append("✅ **Позитивно:** Большинство пользователей довольны приложением.")
        
        recommendations.append("📊 **Анализ:** Изучите детальную аналитику во вкладке 'Аналитика' для глубинного понимания.")
        recommendations.append("📝 **Резюме:** Ознакомьтесь с ИИ-анализом во вкладке 'Резюме' для ключевых инсайтов.")
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")
        
        if results and results.evaluation_report:
            reasoning = results.evaluation_report.analysis.get('reasoning', '')
            if reasoning and reasoning != 'Н/Д':
                st.markdown(f"🤖 **ИИ-оценка:** {reasoning}")
    
    
