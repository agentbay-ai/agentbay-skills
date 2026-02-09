"""
爬取模块
提供基于 wuying-agentbay-sdk 的社交媒体平台爬取功能
"""

from .agentbay_adapter import AgentBayAdapter, create_crawler_session
from .platform_config import PlatformConfig, get_platform_config, SUPPORTED_PLATFORMS
from .crawler import SocialMediaCrawler
from .prompts import build_search_prompt, get_search_prompt_template

__all__ = [
    "AgentBayAdapter",
    "create_crawler_session",
    "PlatformConfig",
    "get_platform_config",
    "SUPPORTED_PLATFORMS",
    "SocialMediaCrawler",
    "build_search_prompt",
    "get_search_prompt_template",
]
