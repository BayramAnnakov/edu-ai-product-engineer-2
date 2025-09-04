import logging
from rapidfuzz import fuzz
from config import SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

class CommentDeduplicator:
    def __init__(self, similarity_threshold=None):
        self.threshold = similarity_threshold or SIMILARITY_THRESHOLD
    
    def normalize_text(self, text):
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def are_similar(self, text1, text2):
        norm_text1 = self.normalize_text(text1)
        norm_text2 = self.normalize_text(text2)
        
        if len(norm_text1) == 0 or len(norm_text2) == 0:
            return False
        
        similarity = fuzz.ratio(norm_text1, norm_text2) / 100.0
        return similarity >= self.threshold
    
    def deduplicate_comments(self, comments):
        if not comments:
            return []
        
        groups = []
        
        for comment in comments:
            comment_text = comment.get("text", "")
            
            assigned_to_group = False
            
            for group in groups:
                representative = group["comments"][0]
                representative_text = representative.get("text", "")
                
                if self.are_similar(comment_text, representative_text):
                    group["comments"].append(comment)
                    group["count"] += 1
                    assigned_to_group = True
                    break
            
            if not assigned_to_group:
                groups.append({
                    "representative_text": comment_text,
                    "comments": [comment],
                    "count": 1
                })
        
        groups.sort(key=lambda x: x["count"], reverse=True)
        
        logger.info(f"Grouped {len(comments)} comments into {len(groups)} similar groups")
        return groups
    
    def format_groups_for_report(self, groups):
        formatted_groups = []
        
        for group in groups:
            representative_text = group["representative_text"]
            count = group["count"]
            
            # Не обрезаем комментарии - показываем полные
            formatted_groups.append({
                "text": representative_text,
                "count": count,
                "comments": group["comments"]  # Добавляем полную информацию о комментариях
            })
        
        return formatted_groups