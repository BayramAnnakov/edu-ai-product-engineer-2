import asyncio
import logging
from datetime import datetime, timedelta
from mcp_tools.youtube import YouTubeMCPClient
from mcp_tools.telegram import TelegramMCPClient
from processors.classifier import CommentClassifier
from processors.deduplicator import CommentDeduplicator
from config import validate_config, DAYS_TO_ANALYZE, USE_AI_CLASSIFICATION, AI_MODEL, YOUTUBE_CHANNEL_ID

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeIntentsAgent:
    def __init__(self):
        self.youtube_client = YouTubeMCPClient()
        self.telegram_client = TelegramMCPClient()
        self.classifier = CommentClassifier(use_ai=USE_AI_CLASSIFICATION)
        self.deduplicator = CommentDeduplicator()
        
    def format_report(self, questions_groups, insights_groups, all_comments):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DAYS_TO_ANALYZE)
        
        classification_method = f"AI-powered ({AI_MODEL})" if USE_AI_CLASSIFICATION else "Rule-based"
        
        # Получаем информацию о видео
        videos_info = {}
        for comment in all_comments:
            video_id = comment.get('video_id')
            video_title = comment.get('video_title')
            if video_id and video_title:
                if video_id not in videos_info:
                    videos_info[video_id] = {"title": video_title, "comment_count": 0}
                videos_info[video_id]["comment_count"] += 1
        
        report = f"""# YouTube Comment Analysis Report
*Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}*
*Classification: {classification_method}*

## 📹 Analyzed Videos ({len(videos_info)} videos, {len(all_comments)} comments total)
"""
        
        for video_id, info in videos_info.items():
            report += f"- **{info['title']}** ({info['comment_count']} комментариев)\n"
        
        report += "\n"
        
        if questions_groups:
            report += f"## 📋 Top Questions ({len(questions_groups)} unique groups)\n"
            for i, group in enumerate(questions_groups[:10], 1):
                count = group["count"]
                text = group["text"]
                # Добавляем информацию о видео для первого комментария в группе
                first_comment = group["comments"][0]
                video_title = first_comment.get("video_title", "Unknown video")
                report += f"{i}. **\"{text}\"** (mentioned {count} time{'s' if count > 1 else ''})\n"
                report += f"   *Из видео: {video_title}*\n\n"
            report += "\n"
        else:
            report += "## 📋 Top Questions\nNo questions found in this period.\n\n"
        
        if insights_groups:
            report += f"## 💡 Top Insights & Suggestions ({len(insights_groups)} unique groups)\n"
            for i, group in enumerate(insights_groups[:10], 1):
                count = group["count"]
                text = group["text"]
                # Добавляем информацию о видео для первого комментария в группе
                first_comment = group["comments"][0]
                video_title = first_comment.get("video_title", "Unknown video")
                report += f"{i}. **\"{text}\"** (mentioned {count} time{'s' if count > 1 else ''})\n"
                report += f"   *Из видео: {video_title}*\n\n"
            report += "\n"
        else:
            report += "## 💡 Top Insights & Suggestions\nNo insights or suggestions found in this period.\n\n"
        
        return report
    
    async def process_comments(self):
        try:
            logger.info("Fetching recent comments from YouTube...")
            comments = await self.youtube_client.get_all_recent_comments()
            
            if not comments:
                logger.warning("No comments found")
                return "No comments found for the specified period."
            
            logger.info(f"Processing {len(comments)} comments...")
            
            classified = self.classifier.classify_comments(comments)
            
            questions_groups = self.deduplicator.deduplicate_comments(classified["questions"])
            insights_groups = self.deduplicator.deduplicate_comments(classified["insights_suggestions"])
            
            formatted_questions = self.deduplicator.format_groups_for_report(questions_groups)
            formatted_insights = self.deduplicator.format_groups_for_report(insights_groups)
            
            report = self.format_report(formatted_questions, formatted_insights, comments)
            
            logger.info("Sending report to Telegram...")
            success = await self.telegram_client.send_report(report, YOUTUBE_CHANNEL_ID)
            
            if success:
                logger.info("Report sent successfully!")
                return "Analysis completed and report sent to Telegram."
            else:
                logger.error("Failed to send report to Telegram")
                return "Analysis completed but failed to send report to Telegram."
                
        except Exception as e:
            logger.error(f"Error processing comments: {e}")
            return f"Error processing comments: {str(e)}"

async def main():
    try:
        validate_config()
        logger.info("Configuration validated successfully")
        
        agent = YouTubeIntentsAgent()
        result = await agent.process_comments()
        
        print(result)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())