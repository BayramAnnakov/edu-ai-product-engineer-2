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
    """Analyze sentiment using VADER"""
    scores = sia.polarity_scores(text)
    
    # Determine overall sentiment
    if scores['compound'] >= 0.05:
        sentiment = 'positive'
    elif scores['compound'] <= -0.05:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    return {
        'sentiment': sentiment,
        'positive_score': scores['pos'],
        'negative_score': scores['neg'],
        'neutral_score': scores['neu'],
        'compound_score': scores['compound']
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
        
        # Compile results
        result = {
            'sentiment': sentiment_results['sentiment'],
            'sentiment_scores': {
                'positive': sentiment_results['positive_score'],
                'negative': sentiment_results['negative_score'],
                'neutral': sentiment_results['neutral_score'],
                'compound': sentiment_results['compound_score']
            },
            'keywords': [{'word': word, 'score': score} for word, score in keywords],
            'top_keywords': [word for word, score in keywords[:5]],
            'feature_categories': feature_categories,
            'top_features': sorted(feature_categories.items(), key=lambda x: x[1], reverse=True)[:3],
            'issues_found': issues,
            'issue_count': len(issues),
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
        all_keywords.extend([kw['word'] for kw in r['keywords']])
    
    top_keywords = Counter(all_keywords).most_common(10)
    
    return {
        'total_reviews': len(results),
        'sentiment_distribution': dict(sentiment_counts),
        'avg_processing_time': round(avg_processing_time, 3),
        'total_issues_found': total_issues,
        'top_keywords_overall': top_keywords,
        'individual_results': results
    }


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