"""
Text utility functions for deterministic analysis
Simple preprocessing and tokenization utilities
"""

import re
from typing import List
from nltk.tokenize import word_tokenize


def clean_text(text: str) -> str:
    """
    Clean text for processing
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove excessive punctuation but keep some for sentence structure
    text = re.sub(r'[!]{2,}', '!', text)  # Multiple exclamation marks
    text = re.sub(r'[?]{2,}', '?', text)  # Multiple question marks
    
    # Remove emojis (basic pattern)
    text = re.sub(r'[^\w\s.,!?-]', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of word tokens
    """
    if not text:
        return []
    
    try:
        tokens = word_tokenize(text)
        # Filter out empty tokens and punctuation-only tokens
        tokens = [token for token in tokens if token.strip() and token.isalnum()]
        return tokens
    except:
        # Fallback to simple split if NLTK fails
        return text.split()