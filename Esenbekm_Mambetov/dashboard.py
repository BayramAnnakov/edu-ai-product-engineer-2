#!/usr/bin/env python3
"""
Refactored Streamlit Dashboard for Hybrid Summarization System.
Clean architecture with separated concerns and proper error handling.
"""

import streamlit as st
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.settings import AppConfig
from src.services.data_service import DataService
from src.ui.components import UIComponents
from src.utils.charts import ChartUtils
from src.utils.logger import Logger


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=AppConfig.APP_TITLE,
        page_icon=AppConfig.APP_ICON,
        layout=AppConfig.LAYOUT,
        initial_sidebar_state=AppConfig.SIDEBAR_STATE
    )


def check_analysis_status():
    """Check if analysis has been completed."""
    data_service = DataService()
    
    # Check if both reviews and results files exist
    has_reviews = data_service.file_exists(AppConfig.DEFAULT_REVIEWS_FILE)
    has_results = data_service.file_exists(AppConfig.DEFAULT_RESULTS_FILE)
    
    return has_reviews and has_results


def load_data():
    """Load data from default files only."""
    data_service = DataService()
    
    reviews_data = None
    results_data = None
    
    # Load from default files only
    if data_service.file_exists(AppConfig.DEFAULT_REVIEWS_FILE):
        reviews_data = data_service.load_reviews_data(AppConfig.DEFAULT_REVIEWS_FILE)
    
    if data_service.file_exists(AppConfig.DEFAULT_RESULTS_FILE):
        results_data = data_service.load_results_data(AppConfig.DEFAULT_RESULTS_FILE)
    
    analysis_complete = reviews_data is not None and results_data is not None
    
    return reviews_data, results_data, analysis_complete


def render_overview_tab(reviews_data, results_data):
    """Render overview tab."""
    UIComponents.render_project_overview(reviews_data, results_data)


def render_summary_tab(results_data):
    """Render summary comparison tab."""
    UIComponents.render_summary_comparison(results_data)


def render_reviews_tab(reviews_data):
    """Render reviews table tab."""
    UIComponents.render_reviews_table(reviews_data)


def render_analytics_tab(reviews_data, results_data):
    """Render analytics tab with charts."""
    st.header("📈 Визуализация данных")
    
    if reviews_data and reviews_data.reviews:
        reviews = reviews_data.reviews
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Rating distribution
            fig_rating = ChartUtils.create_rating_distribution_chart(reviews)
            st.plotly_chart(fig_rating, use_container_width=True)
            
            # Sentiment summary
            fig_sentiment = ChartUtils.create_sentiment_summary_chart(reviews)
            st.plotly_chart(fig_sentiment, use_container_width=True)
        
        with col2:
            # Timeline
            fig_timeline = ChartUtils.create_timeline_chart(reviews)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Rating trend
            fig_trend = ChartUtils.create_rating_trend_chart(reviews)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # Comparison metrics radar chart
        if results_data:
            fig_comparison = ChartUtils.create_comparison_metrics_chart(results_data)
            st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.info("Загрузите данные отзывов для отображения аналитики")


def render_no_data_screen():
    """Render screen when no analysis data is available."""
    st.markdown("""
    # 📊 MBank Reviews Analysis Dashboard
    
    ## ⚠️ Данные анализа не найдены
    
    Для просмотра результатов анализа необходимо сначала выполнить обработку данных.
    
    ### 📋 Инструкция по запуску анализа:
    
    ```bash
    # 1. Установите OpenAI API ключ
    cp .env.example .env
    # Отредактируйте .env и добавьте ваш API ключ
    
    # 2. Запустите анализ
    python main.py analyze --app-id com.maanavan.mb_kyrgyzstan --count 100
    
    # 3. Запустите панель управления
    python run_dashboard.py
    ```
    
    ### 🚀 Быстрый старт:
    ```bash
    python start.py  # Автоматический запуск анализа и панели
    ```
    
    ---
    
    **Ожидаемые файлы:**
    - `results/mbank_reviews.json` - Данные отзывов
    - `results/summary_comparison_results.json` - Результаты анализа
    
    После выполнения анализа обновите эту страницу.
    """)


def main():
    """Main dashboard function."""
    # Initialize logger
    Logger.setup_logger()
    logger = Logger.get_logger()
    
    try:
        # Configure page
        configure_page()
        
        # Render header
        UIComponents.render_page_header()
        
        # Load data and check analysis status
        reviews_data, results_data, analysis_complete = load_data()
        
        # Sidebar with status only
        st.sidebar.title("📊 Статус анализа")
        
        if analysis_complete:
            st.sidebar.success("✅ Данные загружены")
            if reviews_data and reviews_data.metadata:
                st.sidebar.info(f"📱 Приложение: {reviews_data.metadata.app_id}")
                st.sidebar.info(f"📊 Отзывов: {reviews_data.metadata.total_reviews}")
                st.sidebar.info(f"📅 Дата: {reviews_data.metadata.scraped_at[:10]}")
        else:
            st.sidebar.error("❌ Данные не найдены")
            st.sidebar.info("Запустите анализ через CLI")
        
        # Conditional rendering based on analysis status
        if not analysis_complete:
            # Show no data screen with instructions
            render_no_data_screen()
        else:
            # Show full dashboard with navigation tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Обзор", "📝 Резюме", "📱 Отзывы", "📈 Аналитика"
            ])
            
            with tab1:
                render_overview_tab(reviews_data, results_data)
            
            with tab2:
                render_summary_tab(results_data)
            
            with tab3:
                render_reviews_tab(reviews_data)
            
            with tab4:
                render_analytics_tab(reviews_data, results_data)
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📊 MBank Reviews Analysis**")
        st.sidebar.markdown("Read-only dashboard")
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        st.error("Произошла ошибка при загрузке панели управления. Проверьте логи для деталей.")


if __name__ == "__main__":
    main()