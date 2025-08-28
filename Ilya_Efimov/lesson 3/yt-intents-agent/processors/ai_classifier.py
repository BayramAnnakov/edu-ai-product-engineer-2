import logging
from openai import OpenAI
from config import OPENROUTER_API_KEY, AI_MODEL

logger = logging.getLogger(__name__)

class AICommentClassifier:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
    
    def classify_comment_with_ai(self, comment_text):
        """
        AI-powered classification for more accurate categorization.
        Falls back to rule-based classification if API fails.
        """
        try:
            response = self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Classify this YouTube comment into one of these categories:
- "question": Comments asking for information, help, or clarification (questions in any language)
- "insight_suggestion": Comments providing feedback, suggestions, praise, or insights (positive feedback, suggestions, compliments in any language)
- "other": Everything else (spam, off-topic, etc.)

Important: 
- Detect the language of the comment automatically
- Work with Russian, English, and other languages
- Look for question words in Russian: как, что, где, когда, почему, зачем, можно ли, как бы, а что если
- Look for suggestion/praise words in Russian: спасибо, отлично, класс, супер, советую, рекомендую, можно бы, было бы хорошо

Respond with only the category name."""
                    },
                    {
                        "role": "user",
                        "content": comment_text
                    }
                ],
                max_tokens=20,
                temperature=0
            )
            
            classification = response.choices[0].message.content.strip().lower()
            
            if classification in ["question", "insight_suggestion", "other"]:
                return classification
            else:
                return "other"
                
        except Exception as e:
            logger.warning(f"AI classification failed, using fallback: {e}")
            return None