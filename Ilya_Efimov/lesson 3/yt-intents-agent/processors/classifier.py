import re
import logging
from .ai_classifier import AICommentClassifier

logger = logging.getLogger(__name__)

class CommentClassifier:
    def __init__(self, use_ai=False):
        self.use_ai = use_ai
        if use_ai:
            try:
                self.ai_classifier = AICommentClassifier()
            except Exception as e:
                logger.warning(f"AI classifier initialization failed, using rule-based only: {e}")
                self.use_ai = False
        self.question_patterns = [
            # Universal
            r'\?',
            # English patterns
            r'\bhow\b',
            r'\bwhat\b', 
            r'\bwhen\b',
            r'\bwhere\b',
            r'\bwhy\b',
            r'\bwhich\b',
            r'\bwho\b',
            r'\bcan you\b',
            r'\bcould you\b',
            r'\bwould you\b',
            r'\bdo you\b',
            r'\bdid you\b',
            r'\bhave you\b',
            r'\bis there\b',
            r'\bare there\b',
            r'\bwill you\b',
            r'\bshould i\b',
            r'\bcan i\b',
            r'\bhow to\b',
            r'\bplease explain\b',
            r'\bhelp me\b',
            # Russian patterns
            r'\bкак\b',
            r'\bчто\b',
            r'\bгде\b',
            r'\bкогда\b',
            r'\bпочему\b',
            r'\bзачем\b',
            r'\bкто\b',
            r'\bкакой\b',
            r'\bкакая\b',
            r'\bкакое\b',
            r'\bкакие\b',
            r'\bможно ли\b',
            r'\bможете\b',
            r'\bможешь\b',
            r'\bкак бы\b',
            r'\bа что если\b',
            r'\bрасскажите\b',
            r'\bобъясните\b',
            r'\bпомогите\b',
            r'\bскажите\b',
            r'\bподскажите\b',
            r'\bесть ли\b',
            r'\bкуда\b',
            r'\bоткуда\b',
            r'\bсколько\b',
            r'\bкогда будет\b',
            r'\bа как\b'
        ]
        
        self.suggestion_patterns = [
            # English patterns
            r'\byou should\b',
            r'\bi suggest\b',
            r'\bi recommend\b',
            r'\btry\b',
            r'\bconsider\b',
            r'\bmight want to\b',
            r'\bit would be better\b',
            r'\bwhy not\b',
            r'\bhave you tried\b',
            r'\bwhat about\b',
            r'\bmaybe\b',
            r'\bperhaps\b',
            r'\bi think you\b',
            r'\bgreat idea\b',
            r'\bgood point\b',
            r'\bi love\b',
            r'\bawesome\b',
            r'\bamazing\b',
            r'\bbrilliant\b',
            # Russian patterns
            r'\bспасибо\b',
            r'\bблагодарю\b',
            r'\bотлично\b',
            r'\bкласс\b',
            r'\bкруто\b',
            r'\bсупер\b',
            r'\bздорово\b',
            r'\bпрекрасно\b',
            r'\bвеликолепно\b',
            r'\bшикарно\b',
            r'\bумница\b',
            r'\bмолодец\b',
            r'\bсоветую\b',
            r'\bрекомендую\b',
            r'\bможно бы\b',
            r'\bбыло бы хорошо\b',
            r'\bстоило бы\b',
            r'\bпредлагаю\b',
            r'\bлучше бы\b',
            r'\bа не попробовать\b',
            r'\bа что если\b',
            r'\bнравится\b',
            r'\bклёво\b',
            r'\bкайф\b',
            r'\bобожаю\b',
            r'\bвосхитительно\b',
            r'\bпотрясающе\b',
            r'\bфантастика\b',
            r'\bбраво\b',
            r'\bуважение\b',
            r'\bвы правы\b',
            r'\bсогласен\b',
            r'\bсогласна\b',
            r'\bточно\b',
            r'\bименно\b',
            r'\bполезно\b',
            r'\bценно\b',
            r'\bинтересно\b'
        ]
    
    def classify_comment(self, comment_text):
        text_lower = comment_text.lower().strip()
        
        if not text_lower:
            return "other"
        
        # Try AI classification first if available
        if self.use_ai and hasattr(self, 'ai_classifier'):
            ai_result = self.ai_classifier.classify_comment_with_ai(comment_text)
            if ai_result:
                return ai_result
        
        # Fall back to rule-based classification
        question_score = 0
        suggestion_score = 0
        
        for pattern in self.question_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                question_score += 1
        
        for pattern in self.suggestion_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                suggestion_score += 1
        
        if question_score > suggestion_score and question_score > 0:
            return "question"
        elif suggestion_score > 0:
            return "insight_suggestion"
        else:
            return "other"
    
    def classify_comments(self, comments):
        questions = []
        insights_suggestions = []
        other = []
        
        for comment in comments:
            text = comment.get("text", "")
            classification = self.classify_comment(text)
            
            if classification == "question":
                questions.append(comment)
            elif classification == "insight_suggestion":
                insights_suggestions.append(comment)
            else:
                other.append(comment)
        
        logger.info(f"Classified {len(questions)} questions, {len(insights_suggestions)} insights/suggestions, {len(other)} other")
        
        return {
            "questions": questions,
            "insights_suggestions": insights_suggestions,
            "other": other
        }