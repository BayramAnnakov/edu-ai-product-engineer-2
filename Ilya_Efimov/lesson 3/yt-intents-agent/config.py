import os
from dotenv import load_dotenv
from utils.url_parser import extract_channel_id_from_url

load_dotenv()

# Может быть либо URL канала, либо прямой Channel ID
YOUTUBE_CHANNEL_INPUT = os.getenv('YOUTUBE_CHANNEL_URL', os.getenv('YOUTUBE_CHANNEL_ID'))
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Автоматически извлекаем Channel ID из URL если нужно
def get_youtube_channel_id():
    if not YOUTUBE_CHANNEL_INPUT:
        return None
        
    # Если это уже Channel ID (начинается с UC)
    if YOUTUBE_CHANNEL_INPUT.startswith('UC'):
        return YOUTUBE_CHANNEL_INPUT
    
    # Если это URL, извлекаем Channel ID
    if 'youtube.com' in YOUTUBE_CHANNEL_INPUT:
        return extract_channel_id_from_url(YOUTUBE_CHANNEL_INPUT, YOUTUBE_API_KEY)
    
    return YOUTUBE_CHANNEL_INPUT

YOUTUBE_CHANNEL_ID = get_youtube_channel_id()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# AI Configuration
USE_AI_CLASSIFICATION = os.getenv('USE_AI_CLASSIFICATION', 'false').lower() == 'true'
AI_MODEL = os.getenv('AI_MODEL', 'openai/gpt-4o-2024-11-20')

DAYS_TO_ANALYZE = int(os.getenv('DAYS_TO_ANALYZE', 7))
MAX_COMMENTS_PER_VIDEO = int(os.getenv('MAX_COMMENTS_PER_VIDEO', 200))
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.8))

def validate_config():
    # Проверяем основные переменные
    if not YOUTUBE_CHANNEL_ID:
        if not YOUTUBE_CHANNEL_INPUT:
            raise ValueError("Missing YOUTUBE_CHANNEL_URL or YOUTUBE_CHANNEL_ID")
        else:
            raise ValueError(f"Could not extract Channel ID from: {YOUTUBE_CHANNEL_INPUT}")
    
    if not YOUTUBE_API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY")
        
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN")
        
    if not TELEGRAM_CHAT_ID:
        raise ValueError("Missing TELEGRAM_CHAT_ID")
    
    # OpenRouter API key is only required if AI classification is enabled
    if USE_AI_CLASSIFICATION and not OPENROUTER_API_KEY:
        raise ValueError("Missing OPENROUTER_API_KEY (required when USE_AI_CLASSIFICATION=true)")
    
    print(f"✅ Configuration validated")
    print(f"   YouTube Channel ID: {YOUTUBE_CHANNEL_ID}")
    print(f"   AI Classification: {'Enabled' if USE_AI_CLASSIFICATION else 'Disabled'}")
    
    return True