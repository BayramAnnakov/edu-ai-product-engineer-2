"""Chart creation utilities for the dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List

from ..models.review import Review
from ..models.summary import ComparisonResult
from ..config.settings import UIConfig


class ChartUtils:
    """Utility class for creating dashboard charts."""
    
    @staticmethod
    def create_rating_distribution_chart(reviews: List[Review]) -> go.Figure:
        """
        Create rating distribution bar chart.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            Plotly figure
        """
        ratings = [review.rating for review in reviews]
        rating_counts = pd.Series(ratings).value_counts().sort_index()
        
        fig = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            labels={'x': 'Рейтинг', 'y': 'Количество отзывов'},
            title="Распределение рейтингов",
            color=rating_counts.values,
            color_continuous_scale=UIConfig.RATING_COLOR_SCALE
        )
        
        fig.update_layout(
            xaxis_title="Рейтинг (звезды)",
            yaxis_title="Количество отзывов",
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_timeline_chart(reviews: List[Review]) -> go.Figure:
        """
        Create timeline chart of reviews.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            Plotly figure
        """
        dates = [review.date for review in reviews if review.date]
        
        if not dates:
            return go.Figure().add_annotation(
                text="Нет данных для отображения временной динамики",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
        
        date_counts = pd.Series(dates).value_counts().sort_index()
        
        fig = px.line(
            x=date_counts.index,
            y=date_counts.values,
            labels={'x': 'Дата', 'y': 'Количество отзывов'},
            title="Динамика отзывов по времени"
        )
        
        fig.update_layout(
            xaxis_title="Дата",
            yaxis_title="Количество отзывов"
        )
        
        return fig
    
    @staticmethod
    def create_comparison_metrics_chart(results: ComparisonResult) -> go.Figure:
        """
        Create comparison metrics radar chart.
        
        Args:
            results: ComparisonResult object
            
        Returns:
            Plotly figure
        """
        if not results or not results.comparison_metrics:
            return go.Figure().add_annotation(
                text="Нет данных метрик для отображения",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
        
        metrics = results.comparison_metrics
        
        categories = ['Content Overlap', 'Length Ratio', 'Readability Score']
        values = [
            metrics.content_overlap,
            min(metrics.length_ratio, 2.0) / 2.0,  # Normalize to 0-1
            metrics.readability_score
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Метрики сравнения'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            title="Метрики сравнения резюме"
        )
        
        return fig
    
    @staticmethod
    def create_rating_trend_chart(reviews: List[Review]) -> go.Figure:
        """
        Create rating trend over time chart.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            Plotly figure
        """
        if not reviews:
            return go.Figure()
        
        # Create DataFrame
        df = pd.DataFrame([
            {'date': review.date, 'rating': review.rating} 
            for review in reviews if review.date
        ])
        
        if df.empty:
            return go.Figure()
        
        # Convert date and sort
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate moving average
        df['rating_ma'] = df['rating'].rolling(window=10, min_periods=1).mean()
        
        fig = go.Figure()
        
        # Add scatter plot for individual ratings
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['rating'],
            mode='markers',
            name='Отдельные рейтинги',
            opacity=0.6,
            marker=dict(size=4)
        ))
        
        # Add moving average line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['rating_ma'],
            mode='lines',
            name='Скользящее среднее (10 отзывов)',
            line=dict(width=3)
        ))
        
        fig.update_layout(
            title="Тенденция рейтингов во времени",
            xaxis_title="Дата",
            yaxis_title="Рейтинг",
            yaxis=dict(range=[0, 5])
        )
        
        return fig
    
    @staticmethod
    def create_sentiment_summary_chart(reviews: List[Review]) -> go.Figure:
        """
        Create sentiment summary pie chart.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            Plotly figure
        """
        if not reviews:
            return go.Figure()
        
        # Categorize ratings into sentiment
        positive = len([r for r in reviews if r.rating >= 4])
        neutral = len([r for r in reviews if r.rating == 3])
        negative = len([r for r in reviews if r.rating <= 2])
        
        labels = ['Положительные (4-5★)', 'Нейтральные (3★)', 'Отрицательные (1-2★)']
        values = [positive, neutral, negative]
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values,
            marker_colors=colors,
            hole=0.3
        )])
        
        fig.update_layout(
            title="Распределение настроений в отзывах",
            annotations=[dict(text='Настроения', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        return fig