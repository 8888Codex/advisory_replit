"""
Custom Tools for Marketing Legend Agents
Provides specialized capabilities for Disney-level AI experience
"""
from .perplexity_tool import PerplexityResearchTool
from .user_memory_tool import UserMemoryTool
from .story_bank_tool import StoryBankTool
from .youtube_research import YouTubeResearchTool
from .trend_analysis import TrendAnalysisTool
from .news_monitor import NewsMonitorTool

__all__ = [
    "PerplexityResearchTool",
    "UserMemoryTool",
    "StoryBankTool",
    "YouTubeResearchTool",
    "TrendAnalysisTool",
    "NewsMonitorTool"
]
