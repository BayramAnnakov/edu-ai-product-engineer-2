"""
Deterministic Analyzer using NLTK
Handles fast, reproducible analysis of app reviews
"""

import time
import re
import string
from typing import Dict, Any, List, Tuple
from collections import Counter
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('lexicons/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

# Initialize NLTK components
sia = SentimentIntensityAnalyzer()
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# App-specific keywords for categorization
FEATURE_KEYWORDS = {
    'ui_design': ['interface', 'design', 'ui', 'ux', 'layout', 'look', 'appearance', 'visual'],
    'performance': ['speed', 'fast', 'slow', 'lag', 'performance', 'crash', 'freeze', 'bug'],
    'functionality': ['feature', 'function', 'work', 'working', 'functionality', 'capability'],
    'usability': ['easy', 'difficult', 'user-friendly', 'intuitive', 'simple', 'complex'],
    'support': ['support', 'help', 'customer', 'service', 'response', 'team'],
    'content': ['content', 'information', 'data', 'quality', 'accurate', 'updated']
}

ISSUE_KEYWORDS = ['crash', 'bug', 'error', 'problem', 'issue', 'broken', 'fail', 'wrong', 'bad']


def preprocess_text(text: str) -> str:
    """Clean and preprocess text"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def extract_keywords_tfidf(text: str, max_features: int = 10) -> List[Tuple[str, float]]:
    """Extract keywords using TF-IDF"""
    try:
        # Preprocess text
        cleaned_text = preprocess_text(text)
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Fit and transform
        tfidf_matrix = vectorizer.fit_transform([cleaned_text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get top keywords with scores
        keyword_scores = list(zip(feature_names, scores))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        return keyword_scores[:max_features]
    except Exception as e:
        return [("error", 0.0)]


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment using VADER with Russian language support"""
    
    # Russian positive/negative keywords for basic sentiment detection (expanded)
    russian_positive = ['отлично', 'хорошо', 'прекрасно', 'удобно', 'нравится', 'люблю', 'классно', 'супер', 'замечательно', 'великолепно', 'благодарность', 'спасибо', 'лучший', 'интересно', 'полезно', 'рекомендую', 'расширил', 'возможность']
    russian_negative = ['плохо', 'ужасно', 'отстой', 'проблема', 'ошибка', 'баг', 'глюк', 'вылетает', 'тормозит', 'косячный', 'косяк', 'невозможно', 'отвратительно', 'кошмар', 'разочарован', 'жалоба', 'навязчиво', 'думайте', 'неделями', 'напоминать', 'впарит', 'претензией']
    
    text_lower = text.lower()
    
    # Count Russian sentiment words
    russian_pos_count = sum(1 for word in russian_positive if word in text_lower)
    russian_neg_count = sum(1 for word in russian_negative if word in text_lower)
    
    # If Russian text detected, use Russian keyword analysis
    if russian_pos_count > 0 or russian_neg_count > 0:
        # Calculate sentiment based on Russian keywords
        if russian_pos_count > russian_neg_count:
            sentiment = 'POSITIVE'
            compound = 0.5 + (russian_pos_count * 0.1)
        elif russian_neg_count > russian_pos_count:
            sentiment = 'NEGATIVE' 
            compound = -0.5 - (russian_neg_count * 0.1)
        else:
            sentiment = 'NEUTRAL'
            compound = 0.0
            
        # Normalize compound score
        compound = max(-1.0, min(1.0, compound))
        
        return {
            'sentiment': sentiment,
            'confidence': abs(compound),
            'score': compound,
            'positive_score': russian_pos_count / max(1, russian_pos_count + russian_neg_count),
            'negative_score': russian_neg_count / max(1, russian_pos_count + russian_neg_count),
            'neutral_score': 0.1,
            'compound_score': compound,
            'method': 'russian_keywords'
        }
    
    # Fallback to VADER for English text
    scores = sia.polarity_scores(text)
    
    # Determine overall sentiment
    if scores['compound'] >= 0.05:
        sentiment = 'POSITIVE'
    elif scores['compound'] <= -0.05:
        sentiment = 'NEGATIVE'
    else:
        sentiment = 'NEUTRAL'
    
    confidence = abs(scores['compound'])
    
    return {
        'sentiment': sentiment,
        'confidence': confidence,
        'score': scores['compound'],
        'positive_score': scores['pos'],
        'negative_score': scores['neg'],
        'neutral_score': scores['neu'],
        'compound_score': scores['compound'],
        'method': 'vader_english'
    }


def categorize_features(text: str) -> Dict[str, int]:
    """Categorize mentioned features"""
    text_lower = text.lower()
    feature_counts = {}
    
    for category, keywords in FEATURE_KEYWORDS.items():
        count = sum(1 for keyword in keywords if keyword in text_lower)
        feature_counts[category] = count
    
    return feature_counts


def identify_issues(text: str) -> List[str]:
    """Identify potential issues mentioned"""
    text_lower = text.lower()
    found_issues = []
    
    sentences = sent_tokenize(text)
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in ISSUE_KEYWORDS):
            found_issues.append(sentence.strip())
    
    return found_issues


def calculate_readability(text: str) -> Dict[str, Any]:
    """Calculate basic readability metrics"""
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    
    # Filter out punctuation
    words = [word for word in words if word.isalpha()]
    
    if not sentences or not words:
        return {'avg_sentence_length': 0, 'avg_word_length': 0, 'total_words': 0}
    
    avg_sentence_length = len(words) / len(sentences)
    avg_word_length = sum(len(word) for word in words) / len(words)
    
    return {
        'avg_sentence_length': round(avg_sentence_length, 2),
        'avg_word_length': round(avg_word_length, 2),
        'total_words': len(words),
        'total_sentences': len(sentences)
    }


def deterministic_analyze(review_text: str) -> Dict[str, Any]:
    """
    Perform deterministic analysis of app review
    
    Args:
        review_text: The review text to analyze
        
    Returns:
        Dict containing analysis results and metadata
    """
    start_time = time.time()
    
    # Handle empty or None input
    if not review_text or not review_text.strip():
        return {
            'error': 'Empty or invalid text provided',
            'word_count': 0,
            'processing_time': time.time() - start_time
        }
    
    try:
        # Sentiment analysis
        sentiment_results = analyze_sentiment(review_text)
        
        # Keyword extraction
        keywords = extract_keywords_tfidf(review_text)
        
        # Feature categorization
        feature_categories = categorize_features(review_text)
        
        # Issue identification
        issues = identify_issues(review_text)
        
        # Readability metrics
        readability = calculate_readability(review_text)
        
        # Processing time
        processing_time = time.time() - start_time
        
        # Word count for tests
        word_count = len(review_text.split()) if review_text else 0
        
        # Compile results (format expected by tests)
        result = {
            'sentiment': sentiment_results['sentiment'],
            'sentiment_scores': {
                'positive': sentiment_results['positive_score'],
                'negative': sentiment_results['negative_score'],
                'neutral': sentiment_results['neutral_score'],
                'compound': sentiment_results['compound_score']
            },
            'keywords': [word for word, score in keywords[:5]],  # Simple list for tests
            'keywords_detailed': [{'word': word, 'score': score} for word, score in keywords],
            'issues': issues,  # Expected by tests
            'issues_found': issues,  # Keep for compatibility
            'issue_count': len(issues),
            'word_count': word_count,
            'feature_categories': feature_categories,
            'top_features': sorted(feature_categories.items(), key=lambda x: x[1], reverse=True)[:3],
            'readability': readability,
            'processing_time': round(processing_time, 3),
            'reproducible': True,
            'method': 'deterministic_nltk'
        }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'processing_time': time.time() - start_time,
            'method': 'deterministic_nltk'
        }


def generate_deterministic_summary(reviews: List[str]) -> Dict[str, Any]:
    """Generate deterministic summary of all reviews"""
    
    if not reviews:
        return {'error': 'No reviews provided'}
    
    # Analyze all reviews
    results = []
    for review in reviews:
        result = deterministic_analyze(review)
        if 'error' not in result:
            results.append(result)
    
    if not results:
        return {'error': 'No valid analyses'}
    
    # Aggregate sentiment statistics
    sentiments = [r['sentiment'] for r in results]
    sentiment_counts = Counter(sentiments)
    
    # Most common issues
    all_issues = []
    for r in results:
        all_issues.extend(r.get('issues', []))
    
    common_issues = Counter(all_issues).most_common(5)
    
    # Top keywords overall
    all_keywords = []
    for r in results:
        if 'keywords_detailed' in r:
            all_keywords.extend([kw['word'] for kw in r['keywords_detailed']])
    
    top_keywords = Counter(all_keywords).most_common(10)
    
    # Feature analysis
    feature_mentions = {}
    for r in results:
        for feature, count in r.get('feature_categories', {}).items():
            feature_mentions[feature] = feature_mentions.get(feature, 0) + count
    
    # Generate textual summary
    total_reviews = len(results)
    positive_pct = (sentiment_counts.get('POSITIVE', 0) / total_reviews) * 100
    negative_pct = (sentiment_counts.get('NEGATIVE', 0) / total_reviews) * 100
    neutral_pct = (sentiment_counts.get('NEUTRAL', 0) / total_reviews) * 100
    
    summary_text = f"""
ДЕТЕРМИНИСТИЧЕСКИЙ АНАЛИЗ {total_reviews} ОТЗЫВОВ:

📊 НАСТРОЕНИЯ:
- Позитивные: {sentiment_counts.get('POSITIVE', 0)} ({positive_pct:.1f}%)
- Негативные: {sentiment_counts.get('NEGATIVE', 0)} ({negative_pct:.1f}%)  
- Нейтральные: {sentiment_counts.get('NEUTRAL', 0)} ({neutral_pct:.1f}%)

🔍 КЛЮЧЕВЫЕ СЛОВА:
{', '.join([word for word, count in top_keywords[:8]])}

⚠️ ОСНОВНЫЕ ПРОБЛЕМЫ:
{chr(10).join([f"- {issue[:100]}..." if len(issue) > 100 else f"- {issue}" for issue, count in common_issues[:3]])}

🎯 УПОМИНАНИЯ ФУНКЦИЙ:
{', '.join([f"{feature}: {count}" for feature, count in sorted(feature_mentions.items(), key=lambda x: x[1], reverse=True)[:5]])}
""".strip()
    
    return {
        'method': 'deterministic',
        'total_reviews': total_reviews,
        'sentiment_distribution': dict(sentiment_counts),
        'sentiment_percentages': {
            'positive': round(positive_pct, 1),
            'negative': round(negative_pct, 1),
            'neutral': round(neutral_pct, 1)
        },
        'top_keywords': top_keywords[:10],
        'common_issues': common_issues[:5],
        'feature_mentions': feature_mentions,
        'summary_text': summary_text,
        'processing_time': sum(r['processing_time'] for r in results)
    }


def batch_analyze(reviews: List[str]) -> Dict[str, Any]:
    """Analyze multiple reviews and provide aggregate statistics"""
    results = []
    
    for review in reviews:
        result = deterministic_analyze(review)
        if 'error' not in result:
            results.append(result)
    
    if not results:
        return {'error': 'No valid analyses'}
    
    # Aggregate statistics
    sentiments = [r['sentiment'] for r in results]
    sentiment_counts = Counter(sentiments)
    
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
    total_issues = sum(r['issue_count'] for r in results)
    
    # Top keywords across all reviews
    all_keywords = []
    for r in results:
        if 'keywords_detailed' in r:
            all_keywords.extend([kw['word'] for kw in r['keywords_detailed']])
    
    top_keywords = Counter(all_keywords).most_common(10)
    
    return {
        'total_reviews': len(results),
        'sentiment_distribution': dict(sentiment_counts),
        'avg_processing_time': round(avg_processing_time, 3),
        'total_issues_found': total_issues,
        'top_keywords_overall': top_keywords,
        'individual_results': results
    }


# Test-specific functions expected by test suite
def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract keywords using TF-IDF for tests"""
    try:
        keywords_with_scores = extract_keywords_tfidf(text, max_keywords)
        return [kw[0] for kw in keywords_with_scores]
    except:
        # Fallback to simple word frequency
        words = word_tokenize(preprocess_text(text))
        words = [w for w in words if w not in stop_words and len(w) > 2]
        word_freq = Counter(words)
        return [word for word, count in word_freq.most_common(max_keywords)]


def detect_issues(text: str) -> List[Dict[str, str]]:
    """Detect issues in review text for tests"""
    issues = []
    text_lower = text.lower()
    
    for issue_keyword in ISSUE_KEYWORDS:
        if issue_keyword in text_lower:
            issues.append({
                'type': issue_keyword,
                'keyword': issue_keyword,
                'severity': 'medium'  # Default severity
            })
    
    return issues


# Add text utility functions that tests expect
def clean_text(text: str) -> str:
    """Clean text for processing"""
    return preprocess_text(text)


def tokenize(text: str) -> List[str]:
    """Tokenize text into words"""
    return word_tokenize(text)


if __name__ == "__main__":
    # Test the deterministic analyzer
    print("Testing Deterministic Analyzer...")
    
    sample_review = """
    This app is amazing! The interface is so intuitive and easy to use. 
    However, I've noticed that it crashes sometimes when I try to upload large files. 
    The customer support is great though. Overall, I love this app but the crashing issue needs to be fixed.
    """
    
    print("\n📊 Testing Deterministic Analysis...")
    results = deterministic_analyze(sample_review)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
    else:
        print("✅ Deterministic Analysis Results:")
        print(f"Processing time: {results['processing_time']}s")
        print(f"Sentiment: {results['sentiment']} (compound: {results['sentiment_scores']['compound']:.3f})")
        print(f"Top keywords: {results['top_keywords']}")
        print(f"Top features: {results['top_features']}")
        print(f"Issues found: {results['issue_count']}")
        if results['issues_found']:
            print(f"Issue details: {results['issues_found']}")
        print(f"Readability: {results['readability']['avg_sentence_length']:.1f} words/sentence")
        
    # Test batch analysis
    print("\n📈 Testing Batch Analysis...")
    sample_reviews = [
        "Great app! Easy to use and fast.",
        "Terrible experience. App crashes all the time.",
        "Good interface but needs more features."
    ]
    
    batch_results = batch_analyze(sample_reviews)
    if "error" not in batch_results:
        print("✅ Batch Analysis Results:")
        print(f"Total reviews: {batch_results['total_reviews']}")
        print(f"Sentiment distribution: {batch_results['sentiment_distribution']}")
        print(f"Average processing time: {batch_results['avg_processing_time']}s")
        print(f"Top keywords: {batch_results['top_keywords_overall'][:5]}")