import logging
import requests
from datetime import datetime, timedelta
from config import YOUTUBE_CHANNEL_ID, YOUTUBE_API_KEY, DAYS_TO_ANALYZE, MAX_COMMENTS_PER_VIDEO

logger = logging.getLogger(__name__)

class YouTubeAPIClient:
    def __init__(self, channel_id=None):
        self.api_key = YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.channel_id = channel_id or YOUTUBE_CHANNEL_ID
        
    def get_recent_videos(self):
        """Получить последние видео с канала за указанный период"""
        try:
            published_after = (datetime.now() - timedelta(days=DAYS_TO_ANALYZE)).isoformat() + 'Z'
            
            url = f"{self.base_url}/search"
            params = {
                'key': self.api_key,
                'channelId': self.channel_id,
                'part': 'snippet',
                'order': 'date',
                'type': 'video',
                'publishedAfter': published_after,
                'maxResults': 10
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for item in data.get('items', []):
                    video_info = {
                        'id': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'published_at': item['snippet']['publishedAt'],
                        'description': item['snippet']['description']
                    }
                    videos.append(video_info)
                
                logger.info(f"Found {len(videos)} recent videos")
                return videos
            else:
                logger.error(f"YouTube API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching recent videos: {e}")
            return []
    
    def get_video_comments(self, video_id):
        """Получить комментарии к видео"""
        try:
            url = f"{self.base_url}/commentThreads"
            params = {
                'key': self.api_key,
                'videoId': video_id,
                'part': 'snippet',
                'order': 'relevance',
                'maxResults': MAX_COMMENTS_PER_VIDEO,
                'textFormat': 'plainText'
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                comments = []
                
                for item in data.get('items', []):
                    comment_snippet = item['snippet']['topLevelComment']['snippet']
                    
                    comment_info = {
                        'id': item['id'],
                        'text': comment_snippet['textDisplay'],
                        'author': comment_snippet['authorDisplayName'],
                        'like_count': comment_snippet.get('likeCount', 0),
                        'published_at': comment_snippet['publishedAt']
                    }
                    comments.append(comment_info)
                
                logger.info(f"Found {len(comments)} comments for video {video_id}")
                return comments
            else:
                logger.error(f"YouTube API error for video {video_id}: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching comments for video {video_id}: {e}")
            return []
    
    def get_all_recent_comments(self):
        """Получить все комментарии с недавних видео"""
        try:
            videos = self.get_recent_videos()
            all_comments = []
            
            for video in videos:
                video_id = video['id']
                video_title = video['title']
                
                logger.info(f"Fetching comments for: {video_title}")
                comments = self.get_video_comments(video_id)
                
                for comment in comments:
                    comment['video_id'] = video_id
                    comment['video_title'] = video_title
                    
                all_comments.extend(comments)
            
            logger.info(f"Total comments fetched from YouTube API: {len(all_comments)}")
            return all_comments
            
        except Exception as e:
            logger.error(f"Error in get_all_recent_comments: {e}")
            return []