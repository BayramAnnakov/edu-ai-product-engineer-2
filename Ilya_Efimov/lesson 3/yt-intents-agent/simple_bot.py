import asyncio
import logging
import re
import json
import requests
import time
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, validate_config, YOUTUBE_API_KEY
from main import YouTubeIntentsAgent
from utils.url_parser import extract_channel_id_from_url
from mcp_tools.youtube import YouTubeMCPClient
from mcp_tools.telegram import TelegramMCPClient
from processors.classifier import CommentClassifier
from processors.deduplicator import CommentDeduplicator
from config import USE_AI_CLASSIFICATION, AI_MODEL, DAYS_TO_ANALYZE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeIntentsAgentDynamic:
    """Динамический агент для анализа с любым каналом"""
    def __init__(self, channel_id):
        self.channel_id = channel_id
        # Создаем YouTube клиент с переопределенным каналом
        from mcp_tools.youtube_api import YouTubeAPIClient
        if YOUTUBE_API_KEY and YOUTUBE_API_KEY != "demo_youtube_api_key":
            self.youtube_api = YouTubeAPIClient(channel_id=channel_id)
        
        self.telegram_client = TelegramMCPClient()
        self.classifier = CommentClassifier(use_ai=USE_AI_CLASSIFICATION)
        self.deduplicator = CommentDeduplicator()
        
    def format_report(self, questions_groups, insights_groups, all_comments):
        """Копия метода из main.py"""
        from datetime import timedelta
        
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
*Channel ID: {self.channel_id}*

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
                first_comment = group["comments"][0]
                video_title = first_comment.get("video_title", "Unknown video")
                report += f"{i}. **\"{text}\"** (mentioned {count} time{'s' if count > 1 else ''})\n"
                report += f"   *Из видео: {video_title}*\n\n"
            report += "\n"
        else:
            report += "## 💡 Top Insights & Suggestions\nNo insights or suggestions found in this period.\n\n"
        
        return report
    
    async def process_comments(self):
        """Обрабатывает комментарии для заданного канала"""
        try:
            logger.info(f"Fetching recent comments from YouTube for channel: {self.channel_id}")
            
            # Получаем комментарии через API клиент с нашим каналом
            if hasattr(self, 'youtube_api') and self.youtube_api:
                comments = self.youtube_api.get_all_recent_comments()
            else:
                comments = []
            
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
            success = await self.telegram_client.send_report(report, self.channel_id)
            
            if success:
                logger.info("Report sent successfully!")
                return "Analysis completed and report sent to Telegram."
            else:
                logger.error("Failed to send report to Telegram")
                return "Analysis completed but failed to send report to Telegram."
                
        except Exception as e:
            logger.error(f"Error processing comments: {e}")
            return f"Error processing comments: {str(e)}"

class SimpleTelegramBot:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0
        
    def extract_youtube_url_from_message(self, text):
        """Извлекает YouTube URL из текста сообщения"""
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/[@\w\-\.]+',
            r'https?://(?:www\.)?youtube\.com/c/[\w\-\.]+',
            r'https?://(?:www\.)?youtube\.com/channel/[\w\-]+',
            r'https?://(?:www\.)?youtube\.com/user/[\w\-\.]+',
            r'@[\w\-\.]+',
            r'UC[\w\-]+'
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None
    
    def send_message(self, text, parse_mode='Markdown'):
        """Отправляет сообщение в Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to send message: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    def get_updates(self):
        """Получает обновления от Telegram"""
        try:
            url = f"{self.api_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 10
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get updates: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return None
    
    async def process_youtube_channel(self, channel_input, message_id):
        """Обрабатывает анализ YouTube канала"""
        try:
            # Отправляем сообщение о начале анализа
            self.send_message(
                f"🔄 Начинаю анализ канала: `{channel_input}`\n"
                "Это может занять несколько минут..."
            )
            
            # Извлекаем Channel ID
            if channel_input.startswith('UC'):
                channel_id = channel_input
            else:
                channel_id = extract_channel_id_from_url(channel_input, YOUTUBE_API_KEY)
            
            if not channel_id:
                self.send_message(
                    f"❌ Не удалось извлечь ID канала из: `{channel_input}`\n"
                    "Проверьте правильность ссылки и попробуйте еще раз."
                )
                return
            
            # Создаем специальный агент с нужным каналом
            self.send_message(
                f"✅ Канал найден: `{channel_id}`\n"
                "📊 Анализирую комментарии..."
            )
            
            # Создаем агент с динамическим каналом
            agent = YouTubeIntentsAgentDynamic(channel_id)
            result = await agent.process_comments()
            
            self.send_message(
                f"🎉 Анализ завершен!\n"
                f"📋 Результат: {result}"
            )
                
        except Exception as e:
            logger.error(f"Error processing channel {channel_input}: {e}")
            self.send_message(
                f"❌ Ошибка при анализе канала:\n`{str(e)}`"
            )
    
    async def handle_message(self, message):
        """Обработчик входящих сообщений"""
        text = message.get('text', '')
        message_id = message.get('message_id')
        
        if text.startswith('/start'):
            welcome = """🤖 Добро пожаловать в YouTube Analysis Bot!

Я анализирую комментарии YouTube каналов и создаю отчеты.

Команды:
/start - Показать это сообщение  
/help - Показать справку

Просто отправьте ссылку на YouTube канал, и я проанализирую комментарии за последние 7 дней!"""
            self.send_message(welcome)
            
        elif text.startswith('/help'):
            help_text = """📖 Справка по использованию бота

🔗 Поддерживаемые форматы YouTube ссылок:
• https://www.youtube.com/@username
• https://www.youtube.com/c/channelname  
• https://www.youtube.com/channel/UC...
• https://www.youtube.com/user/username
• @username
• UC... (Channel ID)

⚙️ Что я делаю:
• Собираю комментарии за последние 7 дней
• Классифицирую их на вопросы и предложения
• Группирую похожие комментарии
• Отправляю детальный отчет

Просто пришлите ссылку на канал!"""
            self.send_message(help_text)
            
        else:
            # Проверяем, содержит ли сообщение YouTube URL
            youtube_url = self.extract_youtube_url_from_message(text)
            if youtube_url:
                await self.process_youtube_channel(youtube_url, message_id)
            else:
                self.send_message(
                    "❓ Не нашел ссылку на YouTube канал в вашем сообщении.\n\n"
                    "Используйте /help для справки или просто отправьте ссылку на канал."
                )
    
    async def run(self):
        """Основной цикл работы бота"""
        logger.info("Starting simple Telegram bot...")
        
        while True:
            try:
                # Получаем обновления
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    for update in updates.get('result', []):
                        self.last_update_id = update.get('update_id')
                        
                        if 'message' in update:
                            message = update['message']
                            chat_id = str(message['chat']['id'])
                            
                            # Проверяем, что сообщение из нашего чата
                            if chat_id == self.chat_id:
                                await self.handle_message(message)
                
                # Короткая пауза
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                await asyncio.sleep(5)

async def run_simple_bot():
    """Запуск простого бота"""
    try:
        validate_config()
        logger.info("Configuration validated successfully")
        
        bot = SimpleTelegramBot()
        await bot.run()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_simple_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")