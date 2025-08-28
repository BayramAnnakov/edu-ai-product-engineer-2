import re
import requests
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def extract_channel_id_from_url(url, api_key=None):
    """
    Извлекает Channel ID из различных форматов URL YouTube каналов:
    - https://www.youtube.com/@username
    - https://www.youtube.com/c/channelname
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/user/username
    """
    try:
        url = url.strip()
        logger.info(f"Extracting channel ID from: {url}")
        
        # Если URL уже содержит Channel ID (UC...)
        channel_id_match = re.search(r'/channel/([^/?]+)', url)
        if channel_id_match:
            channel_id = channel_id_match.group(1)
            if channel_id.startswith('UC'):
                logger.info(f"Found direct channel ID: {channel_id}")
                return channel_id
        
        # Если это @ формат (новый)
        handle_match = re.search(r'/@([^/?]+)', url)
        if handle_match and api_key:
            handle = handle_match.group(1)
            logger.info(f"Found handle: @{handle}")
            return resolve_handle_to_channel_id(handle, api_key)
        
        # Если это /c/ формат
        custom_match = re.search(r'/c/([^/?]+)', url)
        if custom_match and api_key:
            custom_name = custom_match.group(1)
            logger.info(f"Found custom name: {custom_name}")
            return resolve_custom_name_to_channel_id(custom_name, api_key)
        
        # Если это /user/ формат
        user_match = re.search(r'/user/([^/?]+)', url)
        if user_match and api_key:
            username = user_match.group(1)
            logger.info(f"Found username: {username}")
            return resolve_username_to_channel_id(username, api_key)
            
        # Если ничего не найдено, пытаемся извлечь из HTML страницы
        if api_key is None:
            logger.warning("No API key provided, trying HTML extraction")
            return extract_channel_id_from_html(url)
            
        logger.error(f"Could not extract channel ID from URL: {url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting channel ID: {e}")
        return None

def resolve_handle_to_channel_id(handle, api_key):
    """Преобразует @handle в Channel ID через YouTube API"""
    try:
        # YouTube Data API v3 для handles
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'key': api_key,
            'forHandle': handle,
            'part': 'id'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                channel_id = data['items'][0]['id']
                logger.info(f"Resolved @{handle} to channel ID: {channel_id}")
                return channel_id
        
        logger.error(f"Could not resolve handle @{handle}")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving handle: {e}")
        return None

def resolve_custom_name_to_channel_id(custom_name, api_key):
    """Преобразует custom name в Channel ID через YouTube API"""
    try:
        # YouTube Data API v3 для поиска по имени канала
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'key': api_key,
            'q': custom_name,
            'type': 'channel',
            'part': 'snippet',
            'maxResults': 1
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                channel_id = data['items'][0]['snippet']['channelId']
                logger.info(f"Resolved custom name '{custom_name}' to channel ID: {channel_id}")
                return channel_id
        
        logger.error(f"Could not resolve custom name: {custom_name}")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving custom name: {e}")
        return None

def resolve_username_to_channel_id(username, api_key):
    """Преобразует username в Channel ID через YouTube API"""
    try:
        # YouTube Data API v3 для старых usernames
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'key': api_key,
            'forUsername': username,
            'part': 'id'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                channel_id = data['items'][0]['id']
                logger.info(f"Resolved username '{username}' to channel ID: {channel_id}")
                return channel_id
        
        logger.error(f"Could not resolve username: {username}")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving username: {e}")
        return None

def extract_channel_id_from_html(url):
    """Извлекает Channel ID из HTML страницы канала (fallback метод)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # Ищем Channel ID в различных местах HTML
            patterns = [
                r'"channelId":"([^"]+)"',
                r'"externalId":"([^"]+)"',
                r'meta property="og:url" content="https://www\.youtube\.com/channel/([^"]+)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    channel_id = match.group(1)
                    if channel_id.startswith('UC'):
                        logger.info(f"Extracted channel ID from HTML: {channel_id}")
                        return channel_id
        
        logger.error(f"Could not extract channel ID from HTML: {url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting from HTML: {e}")
        return None