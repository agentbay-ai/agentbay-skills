"""
平台配置模块
支持小红书、微博等社交媒体平台的配置
"""
from dataclasses import dataclass
from typing import List, Optional
@dataclass
class PlatformConfig:
    """平台配置类"""
    # 平台标识
    name: str  # 平台名称，如 "xiaohongshu", "weibo"
    display_name: str  # 显示名称，如 "小红书", "微博"

    # URL配置
    base_url: str  # 平台首页URL
    search_url: str  # 搜索页面URL

    # 搜索相关配置
    search_box_selector: Optional[str] = None  # 搜索框选择器
    search_button_text: List[str] = None  # 搜索按钮文本

    # 内容选择器
    content_selector: Optional[str] = None  # 内容容器选择器
    title_selector: Optional[str] = None  # 标题选择器
    author_selector: Optional[str] = None  # 作者选择器
    time_selector: Optional[str] = None  # 时间选择器

    def __post_init__(self):
        """初始化后处理"""
        if self.search_button_text is None:
            self.search_button_text = ["搜索", "Search"]

    def build_search_url(self, keyword: str) -> str:
        """构造搜索 URL，关键词直接使用中文（由浏览器在请求时编码）。"""
        if self.name == "xhs":
            return f"{self.search_url}?keyword={keyword}&source=web_explore_feed"
        elif self.name == "weibo":
            return f"{self.search_url}?q={keyword}"
        elif self.name == "bing":
            return f"{self.search_url}?q={keyword}"
        elif self.name == "baidu":
            return f"{self.search_url}?rtt=1&bsst=1&cl=2&tn=news&ie=utf-8&word={keyword}"
        else:
            return f"{self.search_url}?keyword={keyword}"


# 平台配置字典
PLATFORM_CONFIGS = {
    "xhs": PlatformConfig(
        name="xhs",
        display_name="小红书",
        base_url="https://www.xiaohongshu.com",
        search_url="https://www.xiaohongshu.com/search_result",
        search_box_selector="input[placeholder*='搜索']",
        search_button_text=["搜索"],
        content_selector=".note-item",
        title_selector=".title",
        author_selector=".author",
        time_selector=".time"
    ),

    "weibo": PlatformConfig(
        name="weibo",
        display_name="微博",
        base_url="https://weibo.com",
        search_url="https://s.weibo.com",
        search_box_selector="input[type='text']",
        search_button_text=["搜索", "Search"],
        content_selector=".card-wrap",
        title_selector=".txt",
        author_selector=".name",
        time_selector=".from"
    ),

    "douyin": PlatformConfig(
        name="douyin",
        display_name="抖音",
        base_url="https://www.douyin.com",
        search_url="https://www.douyin.com/search",
        search_box_selector="input[placeholder*='搜索']",
        search_button_text=["搜索"],
        content_selector=".video-item",
        title_selector=".title",
        author_selector=".author",
        time_selector=".time"
    ),

    "zhihu": PlatformConfig(
        name="zhihu",
        display_name="知乎",
        base_url="https://www.zhihu.com",
        search_url="https://www.zhihu.com/search",
        search_box_selector="input[type='text']",
        search_button_text=["搜索"],
        content_selector=".ContentItem",
        title_selector=".ContentItem-title",
        author_selector=".AuthorInfo-name",
        time_selector=".ContentItem-time"
    ),

    "bing": PlatformConfig(
        name="bing",
        display_name="Bing",
        base_url="https://www.bing.com",
        search_url="https://www.bing.com/search",
        search_box_selector="input[name='q']",
        search_button_text=["搜索", "Search"],
        content_selector="li.b_algo",
        title_selector="h2 a",
        author_selector=None,
        time_selector=None
    ),

    "baidu": PlatformConfig(
        name="baidu",
        display_name="百度",
        base_url="https://www.baidu.com",
        search_url="https://www.baidu.com/s",
        search_box_selector="input[name='wd']",
        search_button_text=["百度一下", "搜索"],
        content_selector=".result-op, .c-container",
        title_selector="h3 a, .c-title a",
        author_selector=None,
        time_selector=None
    ),
}

# 支持的平台列表
SUPPORTED_PLATFORMS = list(PLATFORM_CONFIGS.keys())


def get_platform_config(platform: str) -> PlatformConfig:
    """
    获取平台配置

    Args:
        platform: 平台标识（"xhs", "weibo"等）

    Returns:
        PlatformConfig对象

    Raises:
        ValueError: 如果平台不存在
    """
    if platform not in PLATFORM_CONFIGS:
        available_platforms = ", ".join(PLATFORM_CONFIGS.keys())
        raise ValueError(
            f"不支持的平台: {platform}\n"
            f"支持的平台: {available_platforms}"
        )

    return PLATFORM_CONFIGS[platform]
