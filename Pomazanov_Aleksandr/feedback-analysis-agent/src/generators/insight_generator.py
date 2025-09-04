from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
from datetime import datetime

from ..models.feedback import (
    AnalysisResult, InsightReport, CategoryInsight, 
    FeedbackCategory, Sentiment, Priority
)


class InsightGenerator:
    """Generator for creating insights and reports from analyzed feedback."""
    
    def __init__(self):
        pass
    
    def generate_report(self, analysis_results: List[AnalysisResult]) -> InsightReport:
        """Generate a comprehensive insight report from analysis results."""
        if not analysis_results:
            return self._empty_report()
        
        # Calculate overall statistics
        total_items = len(analysis_results)
        overall_sentiment = self._calculate_overall_sentiment(analysis_results)
        
        # Generate category insights
        category_insights = self._generate_category_insights(analysis_results)
        
        # Find high priority items
        high_priority_items = [
            result for result in analysis_results 
            if result.priority == Priority.HIGH
        ]
        
        # Extract key themes
        key_themes = self._extract_key_themes(analysis_results)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            analysis_results, category_insights, overall_sentiment
        )
        
        return InsightReport(
            generated_at=datetime.now(),
            total_feedback_items=total_items,
            category_insights=category_insights,
            overall_sentiment=overall_sentiment,
            high_priority_items=high_priority_items,
            key_themes=key_themes,
            executive_summary=executive_summary
        )
    
    def _empty_report(self) -> InsightReport:
        """Generate an empty report when no data is available."""
        return InsightReport(
            generated_at=datetime.now(),
            total_feedback_items=0,
            category_insights=[],
            overall_sentiment={Sentiment.POSITIVE: 0.0, Sentiment.NEGATIVE: 0.0, Sentiment.NEUTRAL: 0.0},
            high_priority_items=[],
            key_themes=[],
            executive_summary="No feedback data available for analysis."
        )
    
    def _calculate_overall_sentiment(self, results: List[AnalysisResult]) -> Dict[Sentiment, float]:
        """Calculate overall sentiment distribution."""
        sentiment_counts = Counter(result.sentiment for result in results)
        total = len(results)
        
        return {
            sentiment: count / total 
            for sentiment, count in sentiment_counts.items()
        }
    
    def _generate_category_insights(self, results: List[AnalysisResult]) -> List[CategoryInsight]:
        """Generate insights for each category."""
        category_groups = defaultdict(list)
        
        # Group results by category
        for result in results:
            category_groups[result.category].append(result)
        
        insights = []
        for category, category_results in category_groups.items():
            insight = self._create_category_insight(category, category_results)
            insights.append(insight)
        
        # Sort by count (most common first)
        insights.sort(key=lambda x: x.total_count, reverse=True)
        
        return insights
    
    def _create_category_insight(self, category: FeedbackCategory, results: List[AnalysisResult]) -> CategoryInsight:
        """Create insight for a specific category."""
        total_count = len(results)
        
        # Calculate sentiment distribution
        sentiment_counts = Counter(result.sentiment for result in results)
        sentiment_distribution = {
            sentiment: sentiment_counts.get(sentiment, 0)
            for sentiment in Sentiment
        }
        
        # Calculate priority distribution
        priority_counts = Counter(result.priority for result in results)
        priority_distribution = {
            priority: priority_counts.get(priority, 0)
            for priority in Priority
        }
        
        # Extract top issues (most common actionable items)
        all_actionable_items = []
        for result in results:
            all_actionable_items.extend(result.actionable_items)
        
        top_issues = [
            item for item, count in Counter(all_actionable_items).most_common(5)
        ]
        
        # Generate recommendations
        recommendations = self._generate_category_recommendations(category, results)
        
        return CategoryInsight(
            category=category,
            total_count=total_count,
            sentiment_distribution=sentiment_distribution,
            priority_distribution=priority_distribution,
            top_issues=top_issues,
            recommendations=recommendations
        )
    
    def _generate_category_recommendations(self, category: FeedbackCategory, results: List[AnalysisResult]) -> List[str]:
        """Generate recommendations for a specific category."""
        recommendations = []
        
        # Count high priority items
        high_priority_count = sum(1 for r in results if r.priority == Priority.HIGH)
        negative_sentiment_count = sum(1 for r in results if r.sentiment == Sentiment.NEGATIVE)
        
        # Category-specific recommendations
        if category == FeedbackCategory.BUGS:
            if high_priority_count > 0:
                recommendations.append(f"Address {high_priority_count} critical bug reports immediately")
            recommendations.append("Implement automated testing to prevent similar issues")
            recommendations.append("Set up better error tracking and monitoring")
            
        elif category == FeedbackCategory.PERFORMANCE:
            recommendations.append("Conduct performance audit and optimization")
            recommendations.append("Monitor key performance metrics continuously")
            if high_priority_count > 0:
                recommendations.append("Focus on critical performance bottlenecks first")
                
        elif category == FeedbackCategory.UX_UI:
            recommendations.append("Consider UX/UI redesign for problematic areas")
            recommendations.append("Conduct user testing sessions")
            recommendations.append("Review design system and consistency")
            
        elif category == FeedbackCategory.FEATURE_REQUEST:
            recommendations.append("Prioritize feature requests based on user demand")
            recommendations.append("Create feature roadmap based on feedback")
            recommendations.append("Engage with users for detailed requirements")
            
        elif category == FeedbackCategory.FUNCTIONALITY:
            recommendations.append("Review and improve existing functionality")
            recommendations.append("Update documentation and user guides")
            if negative_sentiment_count > len(results) * 0.5:
                recommendations.append("Consider major functionality overhaul")
        
        # General recommendations based on sentiment
        if negative_sentiment_count > len(results) * 0.6:
            recommendations.append("High negative sentiment - requires immediate attention")
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _extract_key_themes(self, results: List[AnalysisResult]) -> List[str]:
        """Extract key themes from all feedback."""
        # Collect all key phrases
        all_phrases = []
        for result in results:
            all_phrases.extend(result.key_phrases)
        
        # Count phrase frequency
        phrase_counts = Counter(all_phrases)
        
        # Get top themes (most common phrases)
        top_phrases = [phrase for phrase, count in phrase_counts.most_common(10)]
        
        # Group similar themes
        themes = self._group_similar_themes(top_phrases)
        
        return themes[:5]  # Return top 5 themes
    
    def _group_similar_themes(self, phrases: List[str]) -> List[str]:
        """Group similar phrases into themes."""
        # Simple grouping based on common words
        # In a more sophisticated implementation, you could use NLP techniques
        
        themes = []
        used_phrases = set()
        
        for phrase in phrases:
            if phrase in used_phrases:
                continue
                
            # Find similar phrases
            similar_phrases = [phrase]
            phrase_words = set(phrase.lower().split())
            
            for other_phrase in phrases:
                if other_phrase != phrase and other_phrase not in used_phrases:
                    other_words = set(other_phrase.lower().split())
                    # If phrases share words, consider them similar
                    if phrase_words & other_words:
                        similar_phrases.append(other_phrase)
                        used_phrases.add(other_phrase)
            
            # Create theme from similar phrases
            if len(similar_phrases) == 1:
                themes.append(phrase)
            else:
                # Use the most common words as theme
                all_words = []
                for p in similar_phrases:
                    all_words.extend(p.lower().split())
                common_words = [word for word, count in Counter(all_words).most_common(2)]
                themes.append(" ".join(common_words))
            
            used_phrases.add(phrase)
        
        return themes
    
    def _generate_executive_summary(
        self, 
        results: List[AnalysisResult], 
        category_insights: List[CategoryInsight],
        overall_sentiment: Dict[Sentiment, float]
    ) -> str:
        """Generate an executive summary of the feedback analysis."""
        total_items = len(results)
        
        # Find dominant category
        dominant_category = max(category_insights, key=lambda x: x.total_count)
        
        # Calculate key metrics
        high_priority_count = sum(1 for r in results if r.priority == Priority.HIGH)
        negative_sentiment_pct = overall_sentiment.get(Sentiment.NEGATIVE, 0) * 100
        positive_sentiment_pct = overall_sentiment.get(Sentiment.POSITIVE, 0) * 100
        
        # Generate summary
        summary_parts = []
        
        summary_parts.append(f"Analyzed {total_items} feedback items across {len(category_insights)} categories.")
        
        summary_parts.append(
            f"The dominant feedback category is {dominant_category.category.value} "
            f"({dominant_category.total_count} items, {dominant_category.total_count/total_items*100:.1f}%)."
        )
        
        # Sentiment summary
        if negative_sentiment_pct > 50:
            summary_parts.append(f"Overall sentiment is concerning with {negative_sentiment_pct:.1f}% negative feedback.")
        elif positive_sentiment_pct > 50:
            summary_parts.append(f"Overall sentiment is positive with {positive_sentiment_pct:.1f}% positive feedback.")
        else:
            summary_parts.append("Overall sentiment is mixed across positive, negative, and neutral responses.")
        
        # Priority summary
        if high_priority_count > 0:
            summary_parts.append(f"There are {high_priority_count} high-priority items requiring immediate attention.")
        
        # Top recommendation
        if dominant_category.recommendations:
            summary_parts.append(f"Key recommendation: {dominant_category.recommendations[0]}")
        
        return " ".join(summary_parts)