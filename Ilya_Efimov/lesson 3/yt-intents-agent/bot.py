import asyncio
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, validate_config
from main import YouTubeIntentsAgent
from utils.url_parser import extract_channel_id_from_url
from config import YOUTUBE_API_KEY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeBotHandler:
    def __init__(self):
        self.waiting_for_channel = False
        self.agent = None
        
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
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_message = """🤖 Добро пожаловать в YouTube Analysis Bot!

Я анализирую комментарии YouTube каналов и создаю отчеты.

Команды:
/start - Показать это сообщение  
/analyze - Запросить анализ канала
/help - Показать справку

Просто отправьте ссылку на YouTube канал, и я проанализирую комментарии за последние 7 дней!"""
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
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
        
        await update.message.reply_text(help_text)
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /analyze"""
        self.waiting_for_channel = True
        await update.message.reply_text(
            "🔍 Пришлите ссылку на YouTube канал для анализа:\n\n"
            "Например:\n"
            "• https://www.youtube.com/@channelname\n"
            "• @channelname\n" 
            "• https://www.youtube.com/channel/UC...\n\n"
            "Отмена: /cancel"
        )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена ожидания ввода канала"""
        self.waiting_for_channel = False
        await update.message.reply_text("❌ Операция отменена.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик входящих сообщений"""
        text = update.message.text
        
        # Проверяем, содержит ли сообщение YouTube URL
        youtube_url = self.extract_youtube_url_from_message(text)
        
        if youtube_url:
            await self.process_youtube_channel(update, youtube_url)
        else:
            await update.message.reply_text(
                "❓ Не нашел ссылку на YouTube канал в вашем сообщении.\n\n"
                "Используйте /analyze для запуска анализа или /help для справки."
            )
    
    async def process_youtube_channel(self, update: Update, channel_input):
        """Обрабатывает анализ YouTube канала"""
        try:
            # Отправляем сообщение о начале анализа
            status_message = await update.message.reply_text(
                f"🔄 Начинаю анализ канала: `{channel_input}`\n"
                "Это может занять несколько минут...", 
                parse_mode='Markdown'
            )
            
            # Извлекаем Channel ID
            if channel_input.startswith('UC'):
                channel_id = channel_input
            else:
                channel_id = extract_channel_id_from_url(channel_input, YOUTUBE_API_KEY)
            
            if not channel_id:
                await status_message.edit_text(
                    f"❌ Не удалось извлечь ID канала из: `{channel_input}`\n"
                    "Проверьте правильность ссылки и попробуйте еще раз.",
                    parse_mode='Markdown'
                )
                return
            
            # Временно устанавливаем канал в конфигурацию
            import config
            old_channel_id = config.YOUTUBE_CHANNEL_ID
            config.YOUTUBE_CHANNEL_ID = channel_id
            
            try:
                # Создаем и запускаем анализ
                await status_message.edit_text(
                    f"✅ Канал найден: `{channel_id}`\n"
                    "📊 Анализирую комментарии...", 
                    parse_mode='Markdown'
                )
                
                agent = YouTubeIntentsAgent()
                result = await agent.process_comments()
                
                await status_message.edit_text(
                    f"🎉 Анализ завершен!\n"
                    f"📋 Результат: {result}"
                )
                
            finally:
                # Восстанавливаем исходный канал
                config.YOUTUBE_CHANNEL_ID = old_channel_id
                
        except Exception as e:
            logger.error(f"Error processing channel {channel_input}: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при анализе канала:\n`{str(e)}`",
                parse_mode='Markdown'
            )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")

async def run_bot():
    """Запуск Telegram бота"""
    app = None
    try:
        validate_config()
        logger.info("Configuration validated successfully")
        
        # Создаем приложение
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Создаем обработчик
        handler = YouTubeBotHandler()
        
        # Регистрируем команды
        app.add_handler(CommandHandler("start", handler.start))
        app.add_handler(CommandHandler("help", handler.help_command))
        app.add_handler(CommandHandler("analyze", handler.analyze_command))
        app.add_handler(CommandHandler("cancel", handler.cancel_command))
        
        # Обработчик всех текстовых сообщений
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
        
        # Обработчик ошибок
        app.add_error_handler(handler.error_handler)
        
        logger.info("Starting Telegram bot...")
        await app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        
    finally:
        # Корректно закрываем приложение
        if app:
            try:
                await app.shutdown()
            except:
                pass

def main():
    """Основная функция для запуска бота"""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()