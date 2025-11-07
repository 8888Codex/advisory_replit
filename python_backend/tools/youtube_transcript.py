"""
YouTube Transcript Extraction Tool

This module provides functionality to extract video transcripts/subtitles
from YouTube videos using the youtube-transcript-api library.

No API key required - works by scraping YouTube's subtitle data.
"""

from typing import List, Dict, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re


class YouTubeTranscriptTool:
    """
    Tool for extracting transcripts from YouTube videos.
    
    Features:
    - Extract transcripts in multiple languages
    - Format as plain text or structured data
    - Handle auto-generated and manual subtitles
    - Graceful error handling for videos without transcripts
    """
    
    def __init__(self):
        self.formatter = TextFormatter()
    
    def extract_video_id(self, url_or_id: str) -> str:
        """
        Extract video ID from YouTube URL or return ID if already provided.
        
        Args:
            url_or_id: YouTube URL or video ID
            
        Returns:
            Video ID string
            
        Examples:
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
            "dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
        """
        # If already an ID (no slashes or equals), return as-is
        if "/" not in url_or_id and "=" not in url_or_id:
            return url_or_id
        
        # Extract from standard URL
        if "watch?v=" in url_or_id:
            video_id = url_or_id.split("watch?v=")[-1].split("&")[0]
            return video_id
        
        # Extract from shortened URL
        if "youtu.be/" in url_or_id:
            video_id = url_or_id.split("youtu.be/")[-1].split("?")[0]
            return video_id
        
        # If no pattern matched, try to extract with regex
        pattern = r'(?:v=|/)([0-9A-Za-z_-]{11}).*'
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
        
        return url_or_id
    
    def get_transcript(
        self,
        video_id: str,
        languages: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Get transcript as plain text from a YouTube video.
        
        Args:
            video_id: YouTube video ID or URL
            languages: Preferred languages (default: ['pt', 'en'])
            
        Returns:
            Transcript text or None if not available
        """
        if languages is None:
            languages = ['pt', 'pt-BR', 'en', 'es']
        
        try:
            # Extract video ID if URL was provided
            video_id = self.extract_video_id(video_id)
            
            # Get transcript
            transcript_data = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=languages
            )
            
            # Format as plain text
            transcript_text = self.formatter.format_transcript(transcript_data)
            
            return transcript_text
        
        except Exception as e:
            print(f"[YouTubeTranscript] Could not get transcript for {video_id}: {str(e)}")
            return None
    
    def get_transcript_structured(
        self,
        video_id: str,
        languages: Optional[List[str]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get transcript as structured data with timestamps.
        
        Args:
            video_id: YouTube video ID or URL
            languages: Preferred languages (default: ['pt', 'en'])
            
        Returns:
            List of transcript entries with text, start, and duration
            [{'text': '...', 'start': 0.0, 'duration': 2.5}, ...]
        """
        if languages is None:
            languages = ['pt', 'pt-BR', 'en', 'es']
        
        try:
            # Extract video ID if URL was provided
            video_id = self.extract_video_id(video_id)
            
            # Get transcript
            transcript_data = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=languages
            )
            
            return transcript_data
        
        except Exception as e:
            print(f"[YouTubeTranscript] Could not get transcript for {video_id}: {str(e)}")
            return None
    
    def batch_extract_transcripts(
        self,
        video_ids: List[str],
        max_transcripts: int = 10,
        languages: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Extract transcripts from multiple videos.
        
        Args:
            video_ids: List of video IDs or URLs
            max_transcripts: Maximum number of transcripts to extract
            languages: Preferred languages
            
        Returns:
            Dict mapping video_id to transcript text
            {video_id: transcript_text}
        """
        if languages is None:
            languages = ['pt', 'pt-BR', 'en', 'es']
        
        results = {}
        
        for i, video_id in enumerate(video_ids[:max_transcripts]):
            print(f"[YouTubeTranscript] Extracting transcript {i+1}/{min(len(video_ids), max_transcripts)}...")
            
            transcript = self.get_transcript(video_id, languages)
            
            if transcript:
                # Clean video ID
                clean_id = self.extract_video_id(video_id)
                results[clean_id] = transcript
                print(f"[YouTubeTranscript] ✅ Extracted {len(transcript)} characters from {clean_id}")
            else:
                print(f"[YouTubeTranscript] ⚠️ No transcript available for {video_id}")
        
        return results
    
    def get_available_transcripts(self, video_id: str) -> List[Dict[str, Any]]:
        """
        List all available transcripts for a video.
        
        Args:
            video_id: YouTube video ID or URL
            
        Returns:
            List of available transcripts with language info
            [{'language': 'English', 'language_code': 'en', 'is_generated': False}, ...]
        """
        try:
            video_id = self.extract_video_id(video_id)
            
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            available = []
            for transcript in transcript_list:
                available.append({
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated
                })
            
            return available
        
        except Exception as e:
            print(f"[YouTubeTranscript] Could not list transcripts for {video_id}: {str(e)}")
            return []
