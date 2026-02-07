"""
提示词管理模块
从 YAML 文件加载提示词模板
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


# 提示词缓存
_prompts_cache: Dict[str, str] = {}


def _load_prompts() -> Dict[str, str]:
    """
    加载提示词模板

    Returns:
        提示词字典
    """
    global _prompts_cache

    if _prompts_cache:
        return _prompts_cache

    # 获取当前文件所在目录
    current_dir = Path(__file__).parent
    prompts_file = current_dir / "prompts.yaml"

    if not prompts_file.exists():
        raise FileNotFoundError(f"提示词文件不存在: {prompts_file}")

    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts_data = yaml.safe_load(f)

        if not prompts_data:
            raise ValueError("提示词文件为空或格式错误")

        _prompts_cache = prompts_data
        return _prompts_cache

    except yaml.YAMLError as e:
        raise ValueError(f"解析提示词 YAML 文件失败: {e}")
    except Exception as e:
        raise RuntimeError(f"加载提示词文件失败: {e}")


def get_search_prompt_template() -> str:
    """
    获取搜索提示词模板

    Returns:
        提示词模板字符串
    """
    prompts = _load_prompts()
    template = prompts.get("search_prompt_template")

    if not template:
        raise ValueError("未找到 search_prompt_template 提示词模板")

    return template


def get_bing_search_prompt_template() -> str:
    """
    获取 Bing 搜索提示词模板

    Returns:
        Bing 搜索提示词模板字符串
    """
    prompts = _load_prompts()
    template = prompts.get("bing_search_prompt_template")

    if not template:
        raise ValueError("未找到 bing_search_prompt_template 提示词模板")

    return template


def build_search_prompt(
    platform_name: str,
    keyword: str,
    base_url: str,
    search_url: str,
    max_results: int = 50,
    platform_id: Optional[str] = None
) -> str:
    """
    构建搜索提示词。根据 platform_id 选择社交媒体模板或 Bing 模板。

    Args:
        platform_name: 平台名称
        keyword: 搜索关键词
        base_url: 平台基础URL
        search_url: 构造好的搜索URL（已包含关键词）
        max_results: 最大结果数
        platform_id: 平台标识，为 "bing" 时使用 Bing 专用模板，否则使用社交媒体模板

    Returns:
        格式化后的提示词
    """
    if platform_id == "bing":
        template = get_bing_search_prompt_template()
    else:
        template = get_search_prompt_template()

    # 只替换已知占位符，避免模板中 JSON 示例的 { } 被 str.format() 误解析
    out = (
        template.replace("{platform_name}", platform_name)
        .replace("{keyword}", keyword)
        .replace("{base_url}", base_url)
        .replace("{search_url}", search_url)
        .replace("{max_results}", str(max_results))
    )
    # 还原 YAML 中为转义写的双花括号为单花括号（用于 JSON 示例）
    return out.replace("{{", "{").replace("}}", "}")
