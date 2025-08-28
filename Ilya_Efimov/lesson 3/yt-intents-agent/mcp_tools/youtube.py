import logging
from datetime import datetime, timedelta
import subprocess
import json
from config import YOUTUBE_CHANNEL_ID, DAYS_TO_ANALYZE, MAX_COMMENTS_PER_VIDEO, YOUTUBE_API_KEY
from .youtube_api import YouTubeAPIClient

logger = logging.getLogger(__name__)

class YouTubeMCPClient:
    def __init__(self):
        self.server_url = "https://server.smithery.ai/@xianxx17/my-youtube-mcp-server"
        # Initialize YouTube API client if API key is available
        if YOUTUBE_API_KEY and YOUTUBE_API_KEY != "demo_youtube_api_key":
            self.youtube_api = YouTubeAPIClient()
        else:
            self.youtube_api = None
        
    async def get_recent_videos(self):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=DAYS_TO_ANALYZE)
            
            cmd = [
                "mcp",
                "call-tool",
                self.server_url,
                "search_videos",
                json.dumps({
                    "channel_id": YOUTUBE_CHANNEL_ID,
                    "published_after": start_date.isoformat(),
                    "published_before": end_date.isoformat(),
                    "max_results": 50
                })
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("videos", [])
            else:
                logger.error(f"MCP command failed: {result.stderr}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching recent videos: {e}")
            return []
    
    async def get_video_comments(self, video_id):
        try:
            cmd = [
                "mcp",
                "call-tool",
                self.server_url,
                "get-video-comments",
                json.dumps({
                    "video_id": video_id,
                    "max_results": MAX_COMMENTS_PER_VIDEO,
                    "order": "relevance"
                })
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                comments = data.get("comments", [])
                
                top_level_comments = []
                for comment in comments:
                    if comment.get("parent_id") is None:
                        top_level_comments.append({
                            "id": comment.get("id"),
                            "text": comment.get("text", ""),
                            "author": comment.get("author", "Unknown"),
                            "like_count": comment.get("like_count", 0),
                            "published_at": comment.get("published_at", "")
                        })
                
                return top_level_comments[:MAX_COMMENTS_PER_VIDEO]
            else:
                logger.error(f"MCP command failed: {result.stderr}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching comments for video {video_id}: {e}")
            return []
    
    async def get_all_recent_comments(self):
        try:
            # Try YouTube API first if available
            if self.youtube_api:
                logger.info("Using YouTube Data API to fetch comments")
                all_comments = self.youtube_api.get_all_recent_comments()
                
                if all_comments:
                    logger.info(f"Successfully fetched {len(all_comments)} comments from YouTube API")
                    return all_comments
                else:
                    logger.warning("YouTube API returned no comments")
            
            # Fallback to MCP if YouTube API is not available
            logger.info("Trying MCP servers...")
            videos = await self.get_recent_videos()
            all_comments = []
            
            for video in videos:
                video_id = video.get("id")
                video_title = video.get("title", "Unknown")
                
                logger.info(f"Fetching comments for: {video_title}")
                comments = await self.get_video_comments(video_id)
                
                for comment in comments:
                    comment["video_id"] = video_id
                    comment["video_title"] = video_title
                    
                all_comments.extend(comments)
            
            # Final fallback to mock data for demonstration
            if not all_comments:
                logger.warning("No comments from MCP or YouTube API, using mock data for demonstration")
                from .mock_data import get_mock_comments
                all_comments = get_mock_comments()
            
            logger.info(f"Total comments fetched: {len(all_comments)}")
            return all_comments
            
        except Exception as e:
            logger.error(f"Error in get_all_recent_comments: {e}")
            # Use mock data as fallback
            logger.info("Using mock data as fallback")
            from .mock_data import get_mock_comments
            return get_mock_comments()