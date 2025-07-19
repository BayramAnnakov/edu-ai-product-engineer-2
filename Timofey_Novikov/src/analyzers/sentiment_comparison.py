"""
Sentiment Analysis Comparison Module
Compares deterministic vs LLM vs Agent sentiment analysis results
"""

from typing import Dict, Any, List, Tuple
from collections import Counter


def compare_sentiment_methods(batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare sentiment analysis results from different methods
    
    Args:
        batch_results: List of analysis results from batch processing
        
    Returns:
        Dict containing comparison metrics and analysis
    """
    
    if not batch_results:
        return {'error': 'No results provided for comparison'}
    
    # Extract sentiment results from each method
    deterministic_sentiments = []
    llm_sentiments = []
    agent_sentiments = []
    
    for result in batch_results:
        if 'error' not in result:
            # Deterministic sentiment
            det_sentiment = result.get('deterministic_results', {}).get('sentiment', 'UNKNOWN')
            deterministic_sentiments.append(det_sentiment)
            
            # LLM sentiment  
            llm_sentiment = result.get('llm_results', {}).get('sentiment', 'Unknown')
            llm_sentiments.append(llm_sentiment)
            
            # Agent sentiment
            agent_sentiment = result.get('agent_results', {}).get('sentiment_analysis', {}).get('sentiment', 'UNKNOWN')
            agent_sentiments.append(agent_sentiment)
    
    total_reviews = len(deterministic_sentiments)
    
    if total_reviews == 0:
        return {'error': 'No valid sentiment results found'}
    
    # Count sentiment distributions
    det_counts = Counter(deterministic_sentiments)
    llm_counts = Counter(llm_sentiments)
    agent_counts = Counter(agent_sentiments)
    
    # Calculate agreement metrics
    exact_matches = 0
    det_llm_matches = 0
    det_agent_matches = 0
    llm_agent_matches = 0
    
    for i in range(total_reviews):
        det = deterministic_sentiments[i]
        llm = llm_sentiments[i]
        agent = agent_sentiments[i]
        
        # Normalize sentiments for comparison
        det_norm = normalize_sentiment(det)
        llm_norm = normalize_sentiment(llm)
        agent_norm = normalize_sentiment(agent)
        
        # Count matches
        if det_norm == llm_norm == agent_norm:
            exact_matches += 1
        
        if det_norm == llm_norm:
            det_llm_matches += 1
            
        if det_norm == agent_norm:
            det_agent_matches += 1
            
        if llm_norm == agent_norm:
            llm_agent_matches += 1
    
    # Calculate percentages
    exact_agreement = (exact_matches / total_reviews) * 100
    det_llm_agreement = (det_llm_matches / total_reviews) * 100
    det_agent_agreement = (det_agent_matches / total_reviews) * 100
    llm_agent_agreement = (llm_agent_matches / total_reviews) * 100
    
    # Identify disagreements
    disagreements = []
    for i, result in enumerate(batch_results):
        if 'error' not in result:
            det = normalize_sentiment(deterministic_sentiments[i])
            llm = normalize_sentiment(llm_sentiments[i])
            agent = normalize_sentiment(agent_sentiments[i])
            
            if not (det == llm == agent):
                review_text = result.get('review_text', '')[:100] + "..."
                disagreements.append({
                    'review_index': i,
                    'review_preview': review_text,
                    'deterministic': det,
                    'llm': llm,
                    'agent': agent
                })
    
    # Generate comparison text
    comparison_text = f"""
СРАВНЕНИЕ МЕТОДОВ АНАЛИЗА НАСТРОЕНИЙ ({total_reviews} отзывов):

📊 РАСПРЕДЕЛЕНИЕ ПО МЕТОДАМ:
Детерминистический: {format_sentiment_distribution(det_counts)}
LLM (GPT-4): {format_sentiment_distribution(llm_counts)}
Агенты: {format_sentiment_distribution(agent_counts)}

🤝 СОГЛАСОВАННОСТЬ МЕТОДОВ:
- Полное согласие всех методов: {exact_agreement:.1f}%
- Детерминистический ↔ LLM: {det_llm_agreement:.1f}%
- Детерминистический ↔ Агенты: {det_agent_agreement:.1f}%
- LLM ↔ Агенты: {llm_agent_agreement:.1f}%

⚠️ РАСХОЖДЕНИЙ: {len(disagreements)} из {total_reviews} отзывов

📈 ВЫВОДЫ:
{generate_sentiment_insights(det_counts, llm_counts, agent_counts, exact_agreement)}
""".strip()
    
    return {
        'total_reviews': total_reviews,
        'sentiment_distributions': {
            'deterministic': dict(det_counts),
            'llm': dict(llm_counts),
            'agent': dict(agent_counts)
        },
        'agreement_metrics': {
            'exact_agreement_percentage': round(exact_agreement, 1),
            'deterministic_llm_agreement': round(det_llm_agreement, 1),
            'deterministic_agent_agreement': round(det_agent_agreement, 1),
            'llm_agent_agreement': round(llm_agent_agreement, 1)
        },
        'disagreements': disagreements[:10],  # Show first 10 disagreements
        'total_disagreements': len(disagreements),
        'comparison_text': comparison_text,
        'method': 'sentiment_comparison'
    }


def normalize_sentiment(sentiment: str) -> str:
    """Normalize sentiment values for comparison"""
    sentiment_lower = sentiment.lower()
    
    if sentiment_lower in ['positive', 'pos', 'good']:
        return 'positive'
    elif sentiment_lower in ['negative', 'neg', 'bad']:
        return 'negative'
    elif sentiment_lower in ['neutral', 'neut', 'mixed']:
        return 'neutral'
    else:
        return 'unknown'


def format_sentiment_distribution(counts: Counter) -> str:
    """Format sentiment distribution for display"""
    total = sum(counts.values())
    if total == 0:
        return "No data"
    
    items = []
    for sentiment in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
        count = counts.get(sentiment, 0)
        percentage = (count / total) * 100
        items.append(f"{sentiment.lower()}: {count} ({percentage:.1f}%)")
    
    # Add any other sentiments
    for sentiment, count in counts.items():
        if sentiment not in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
            percentage = (count / total) * 100
            items.append(f"{sentiment.lower()}: {count} ({percentage:.1f}%)")
    
    return ", ".join(items)


def generate_sentiment_insights(det_counts: Counter, llm_counts: Counter, agent_counts: Counter, exact_agreement: float) -> str:
    """Generate insights from sentiment comparison"""
    
    insights = []
    
    # Agreement level analysis
    if exact_agreement > 70:
        insights.append("Высокая согласованность между методами")
    elif exact_agreement > 50:
        insights.append("Умеренная согласованность между методами")
    else:
        insights.append("Низкая согласованность - методы часто расходятся")
    
    # Method bias analysis
    det_positive_ratio = det_counts.get('POSITIVE', 0) / max(1, sum(det_counts.values()))
    llm_positive_ratio = llm_counts.get('Positive', 0) / max(1, sum(llm_counts.values()))
    agent_positive_ratio = agent_counts.get('POSITIVE', 0) / max(1, sum(agent_counts.values()))
    
    if det_positive_ratio > 0.6:
        insights.append("Детерминистический метод склонен к позитивным оценкам")
    elif det_positive_ratio < 0.3:
        insights.append("Детерминистический метод склонен к негативным оценкам")
    
    if llm_positive_ratio > 0.6:
        insights.append("LLM склонен к позитивным оценкам")
    elif llm_positive_ratio < 0.3:
        insights.append("LLM склонен к негативным оценкам")
    
    if agent_positive_ratio > 0.6:
        insights.append("Агенты склонны к позитивным оценкам")
    elif agent_positive_ratio < 0.3:
        insights.append("Агенты склонны к негативным оценкам")
    
    return "; ".join(insights) if insights else "Методы показывают сбалансированные результаты"