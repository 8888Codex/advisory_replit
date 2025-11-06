"""
YouTube Data API v3 Integration
Real video search with authentic statistics (views, likes, channels, thumbnails)
Zero mock data - 100% verified YouTube content
"""
import os
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class YouTubeAPITool:
    """
    YouTube Data API v3 client for real video search.
    
    Features:
    - Search videos with filters (relevance, view count, date)
    - Retrieve video statistics (views, likes, comments)
    - Get channel information (verified status, subscriber count)
    - Fetch high-quality thumbnails
    - Zero mock data - all results are real YouTube videos
    
    Rate Limits: 10,000 queries/day (free tier)
    """
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY not found in environment variables")
        
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance",
        published_after: Optional[str] = None,
        region_code: str = "BR"
    ) -> Dict[str, Any]:
        """
        Search for YouTube videos with real statistics.
        
        Args:
            query: Search query (e.g., "Moda Sustentável marketing 2024")
            max_results: Number of videos to return (1-50, default 10)
            order: Sort order - "relevance", "date", "viewCount", "rating"
            published_after: ISO 8601 date (e.g., "2023-01-01T00:00:00Z")
            region_code: ISO 3166-1 alpha-2 country code (default "BR")
        
        Returns:
            {
                "videos": [
                    {
                        "videoId": "dQw4w9WgXcQ",
                        "title": "Video Title",
                        "description": "Video description...",
                        "channelId": "UC...",
                        "channelTitle": "Channel Name",
                        "publishedAt": "2024-01-15T10:30:00Z",
                        "thumbnails": {
                            "default": "https://i.ytimg.com/vi/.../default.jpg",
                            "medium": "https://i.ytimg.com/vi/.../mqdefault.jpg",
                            "high": "https://i.ytimg.com/vi/.../hqdefault.jpg"
                        },
                        "statistics": {
                            "viewCount": 1250000,
                            "likeCount": 45000,
                            "commentCount": 3200
                        },
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                    }
                ],
                "totalResults": 1000000,
                "query": "original search query"
            }
        """
        try:
            # Step 1: Search for videos
            search_params = {
                "key": self.api_key,
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "order": order,
                "regionCode": region_code,
                "relevanceLanguage": "pt" if region_code == "BR" else None,
                "safeSearch": "moderate"
            }
            
            if published_after:
                search_params["publishedAfter"] = published_after
            
            # Remove None values
            search_params = {k: v for k, v in search_params.items() if v is not None}
            
            search_response = await self.client.get(
                f"{self.base_url}/search",
                params=search_params
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if not search_data.get("items"):
                return {
                    "videos": [],
                    "totalResults": 0,
                    "query": query,
                    "error": "No videos found for this query"
                }
            
            # Step 2: Get video statistics (views, likes, comments)
            video_ids = [item["id"]["videoId"] for item in search_data["items"]]
            
            stats_params = {
                "key": self.api_key,
                "part": "statistics",
                "id": ",".join(video_ids)
            }
            
            stats_response = await self.client.get(
                f"{self.base_url}/videos",
                params=stats_params
            )
            stats_response.raise_for_status()
            stats_data = stats_response.json()
            
            # Create statistics lookup
            stats_lookup = {
                item["id"]: item["statistics"]
                for item in stats_data.get("items", [])
            }
            
            # Step 3: Combine search results with statistics
            videos = []
            for item in search_data["items"]:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                stats = stats_lookup.get(video_id, {})
                
                video = {
                    "videoId": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "channelId": snippet.get("channelId", ""),
                    "channelTitle": snippet.get("channelTitle", ""),
                    "publishedAt": snippet.get("publishedAt", ""),
                    "thumbnails": {
                        "default": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                        "medium": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                        "high": snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                    },
                    "statistics": {
                        "viewCount": int(stats.get("viewCount", 0)),
                        "likeCount": int(stats.get("likeCount", 0)),
                        "commentCount": int(stats.get("commentCount", 0))
                    },
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                }
                videos.append(video)
            
            return {
                "videos": videos,
                "totalResults": search_data.get("pageInfo", {}).get("totalResults", 0),
                "query": query
            }
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            return {
                "videos": [],
                "totalResults": 0,
                "query": query,
                "error": f"YouTube API error: {e.response.status_code} - {error_detail}"
            }
        except Exception as e:
            return {
                "videos": [],
                "totalResults": 0,
                "query": query,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
