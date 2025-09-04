import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import json
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeeklyScheduler:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.schedule_file = "schedule_state.json"
        self.last_request_time = self.load_last_request_time()
    
    def load_last_request_time(self):
        """Загружает время последнего запроса из файла"""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data.get('last_request_time', '2000-01-01'))
            return datetime(2000, 1, 1)  # Далекое прошлое для первого запуска
        except Exception as e:
            logger.error(f"Error loading schedule state: {e}")
            return datetime(2000, 1, 1)
    
    def save_last_request_time(self, timestamp):
        """Сохраняет время последнего запроса в файл"""
        try:
            data = {
                'last_request_time': timestamp.isoformat(),
                'next_request_time': (timestamp + timedelta(weeks=1)).isoformat()
            }
            with open(self.schedule_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving schedule state: {e}")
    
    def should_send_weekly_request(self):
        """Проверяет, нужно ли отправлять еженедельный запрос в субботу в 9 утра UTC+3"""
        from datetime import timezone
        
        # UTC+3 timezone
        utc_plus_3 = timezone(timedelta(hours=3))
        now = datetime.now(utc_plus_3)
        
        # Проверяем, что сегодня суббота (weekday() == 5) и время >= 9:00
        if now.weekday() != 5:  # Не суббота
            return False
            
        if now.hour < 9:  # Еще не 9 утра
            return False
        
        # Проверяем, не отправляли ли уже на этой неделе
        # Находим последнюю субботу в 9:00
        days_since_saturday = (now.weekday() + 2) % 7  # 0 = суббота
        last_saturday_9am = now.replace(hour=9, minute=0, second=0, microsecond=0) - timedelta(days=days_since_saturday)
        
        # Если сегодня суббота после 9 утра, используем сегодняшнюю дату
        if now.weekday() == 5 and now.hour >= 9:
            current_saturday_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
            return self.last_request_time < current_saturday_9am
        
        return self.last_request_time < last_saturday_9am
    
    def get_next_saturday_9am_utc3(self):
        """Возвращает дату и время следующей субботы в 9:00 UTC+3"""
        from datetime import timezone
        
        utc_plus_3 = timezone(timedelta(hours=3))
        now = datetime.now(utc_plus_3)
        
        # Вычисляем дни до следующей субботы
        days_until_saturday = (5 - now.weekday()) % 7  # 5 = суббота
        
        # Если сегодня суббота, но еще не 9:00, используем сегодня
        if now.weekday() == 5 and now.hour < 9:
            next_saturday = now.replace(hour=9, minute=0, second=0, microsecond=0)
        # Если сегодня суббота и уже после 9:00, следующая суббота через неделю
        elif now.weekday() == 5:
            next_saturday = (now + timedelta(weeks=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        # Иначе находим ближайшую субботу
        else:
            if days_until_saturday == 0:  # Если уже прошла суббота на этой неделе
                days_until_saturday = 7
            next_saturday = (now + timedelta(days=days_until_saturday)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        return next_saturday
    
    async def send_weekly_request(self):
        """Отправляет еженедельный запрос на анализ канала"""
        try:
            message = """🗓 Еженедельный анализ YouTube каналов
⏰ Каждую субботу в 9:00 (UTC+3)

Какой канал проанализировать сегодня? 

Пришлите ссылку на YouTube канал:
• https://www.youtube.com/@channelname
• @channelname  
• https://www.youtube.com/channel/UC...

Я проанализирую комментарии за последние 7 дней и отправлю подробный отчет! 📊"""

            await self.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )
            
            # Сохраняем время отправки запроса
            now = datetime.now()
            self.save_last_request_time(now)
            self.last_request_time = now
            
            logger.info("Weekly request sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending weekly request: {e}")
            return False
    
    async def run_scheduler_check(self):
        """Однократная проверка и отправка запроса при необходимости"""
        if self.should_send_weekly_request():
            logger.info("Time for weekly request - sending...")
            await self.send_weekly_request()
        else:
            next_saturday = self.get_next_saturday_9am_utc3()
            logger.info(f"Next weekly request scheduled for: {next_saturday.strftime('%Y-%m-%d %H:%M UTC+3 (Saturday)')}")
    
    async def run_continuous_scheduler(self):
        """Непрерывный планировщик (запускается в фоне)"""
        logger.info("Starting continuous weekly scheduler...")
        
        while True:
            try:
                await self.run_scheduler_check()
                
                # Проверяем каждый час
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in continuous scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

class SchedulerManager:
    """Менеджер для запуска планировщика в разных режимах"""
    
    @staticmethod
    async def run_once():
        """Однократная проверка планировщика"""
        scheduler = WeeklyScheduler()
        await scheduler.run_scheduler_check()
    
    @staticmethod 
    async def run_continuous():
        """Непрерывная работа планировщика"""
        scheduler = WeeklyScheduler()
        await scheduler.run_continuous_scheduler()
    
    @staticmethod
    async def force_send_request():
        """Принудительная отправка запроса (для тестирования)"""
        scheduler = WeeklyScheduler()
        result = await scheduler.send_weekly_request()
        if result:
            print("✅ Weekly request sent successfully")
        else:
            print("❌ Failed to send weekly request")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "once":
            asyncio.run(SchedulerManager.run_once())
        elif sys.argv[1] == "force":
            asyncio.run(SchedulerManager.force_send_request())
        elif sys.argv[1] == "continuous":
            asyncio.run(SchedulerManager.run_continuous())
        else:
            print("Usage: python scheduler.py [once|force|continuous]")
    else:
        # По умолчанию - однократная проверка
        asyncio.run(SchedulerManager.run_once())