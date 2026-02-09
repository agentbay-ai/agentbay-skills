"""
社交媒体爬取器
使用 AgentBay 进行内容爬取
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agentbay_adapter import AgentBayAdapter
from .platform_config import PlatformConfig, get_platform_config
from .prompts import build_search_prompt


class SocialMediaCrawler:
    """社交媒体爬取器"""

    def __init__(self, adapter: AgentBayAdapter, platform_config: PlatformConfig):
        """
        初始化爬取器

        Args:
            adapter: AgentBay适配器
            platform_config: 平台配置
        """
        self.adapter = adapter
        self.platform_config = platform_config

    def _build_search_prompt(self, keyword: str, max_results: int = 50) -> str:
        """
        构建搜索提示词

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数

        Returns:
            搜索提示词
        """
        # 构造搜索URL
        search_url = self.platform_config.build_search_url(keyword)

        return build_search_prompt(
            platform_name=self.platform_config.display_name,
            keyword=keyword,
            base_url=self.platform_config.base_url,
            search_url=search_url,
            max_results=max_results,
            platform_id=self.platform_config.name
        )

    async def crawl_by_keyword(
        self,
        keyword: str,
        max_results: int = 50,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        根据关键词爬取内容

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            timeout: 超时时间（秒）

        Returns:
            爬取结果
        """
        print(f"\n{'='*60}")
        print(f"🔍 开始爬取 {self.platform_config.display_name} 平台")
        print(f"关键词: {keyword}")
        print(f"最大结果数: {max_results}")
        print(f"{'='*60}\n")

        # 结果文件由 Agent 按 JSON Lines 格式写入（每行一条，append 追加），无需预先创建

        # 构建搜索提示词
        prompt = self._build_search_prompt(keyword, max_results)

        # 执行爬取任务
        result = await self.adapter.execute_crawl_task(prompt, timeout)

        # 任务结束后从会话文件系统读取 /tmp/results.json（支持 JSON 数组或 JSON Lines）
        # 即使任务被标记为 success: false（如 Agent 因未满 30 条调用了 done(success: false)），
        # 仍尝试读取文件，若有数据则视为部分成功，避免丢弃已抓取内容
        results_from_file = None
        if self.adapter.session:
            try:
                print("📂 正在从会话读取 /tmp/results.json ...")
                file_result = await self.adapter.session.file_system.read_file("/tmp/results.json")
                if file_result.success:
                    raw = (file_result.content or "").strip()
                    if raw:
                        try:
                            # 兼容多种格式：
                            # 1) 整份为 JSON 数组 [ ... ]
                            if raw.strip().startswith("["):
                                results_from_file = json.loads(raw)
                                if not isinstance(results_from_file, list):
                                    results_from_file = None
                            else:
                                lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
                                results_from_file = []
                                # 2) 首行为 Agent 写的 header（以 "results":[ 结尾），其余每行一条 result JSON
                                if lines and lines[0].rstrip().endswith('"results":['):
                                    for line in lines[1:]:
                                        try:
                                            results_from_file.append(json.loads(line))
                                        except json.JSONDecodeError:
                                            pass
                                else:
                                    # 3) 纯 JSONL：每行一条完整 JSON
                                    for line in lines:
                                        try:
                                            results_from_file.append(json.loads(line))
                                        except json.JSONDecodeError:
                                            pass
                            if results_from_file is not None:
                                print(f"📄 已读取 /tmp/results.json，共 {len(results_from_file)} 条结果")
                        except json.JSONDecodeError as e:
                            print(f"⚠️ /tmp/results.json 解析失败: {e}，将使用任务返回结果")
                            results_from_file = None
                    else:
                        results_from_file = []
                        print("📄 已读取 /tmp/results.json，内容为空")
                else:
                    print(f"⚠️ 读取 /tmp/results.json 失败: {getattr(file_result, 'error_message', 'unknown')}")
            except Exception as e:
                print(f"⚠️ 读取 /tmp/results.json 异常: {e}，将使用任务返回结果")

        # 若任务标记为失败且未从文件读到任何结果，则直接返回失败
        if not result.get("success") and not (
            results_from_file is not None
            and isinstance(results_from_file, list)
            and len(results_from_file) > 0
        ):
            return result

        # 解析结果
        task_result = result.get("result", {})

        # 只要成功从文件读到列表（含空列表），就以文件为准
        if results_from_file is not None and isinstance(results_from_file, list):
            task_result = {
                "success": True,
                "platform": self.platform_config.name,
                "keyword": keyword,
                "total_count": len(results_from_file),
                "results": results_from_file
            }
            if len(results_from_file) > 0:
                print(f"✅ 已使用 /tmp/results.json 中的结果，共 {len(results_from_file)} 条")

        # 如果结果是字符串，尝试解析JSON
        if isinstance(task_result, str):
            try:
                task_result = json.loads(task_result)
            except json.JSONDecodeError:
                # 如果不是JSON，尝试从原始结果中提取
                task_result = {
                    "success": True,
                    "platform": self.platform_config.name,
                    "keyword": keyword,
                    "total_count": 0,
                    "results": []
                }

        # 确保结果格式正确
        if not isinstance(task_result, dict):
            task_result = {
                "success": True,
                "platform": self.platform_config.name,
                "keyword": keyword,
                "total_count": 0,
                "results": []
            }

        # 添加元数据
        task_result["crawl_time"] = datetime.now().isoformat()
        task_result["platform"] = self.platform_config.name
        task_result["platform_display"] = self.platform_config.display_name

        # 确保results是列表
        if "results" not in task_result or not isinstance(task_result["results"], list):
            task_result["results"] = []

        print(f"✅ 爬取完成，共获取 {len(task_result.get('results', []))} 条结果\n")

        return {
            "success": True,
            **task_result
        }

    async def crawl_multiple_keywords(
        self,
        keywords: List[str],
        max_results_per_keyword: int = 50,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        爬取多个关键词

        Args:
            keywords: 关键词列表
            max_results_per_keyword: 每个关键词的最大结果数
            timeout: 超时时间（秒）

        Returns:
            合并后的爬取结果
        """
        all_results = []

        for i, keyword in enumerate(keywords, 1):
            print(f"\n处理关键词 {i}/{len(keywords)}: {keyword}")

            result = await self.crawl_by_keyword(
                keyword=keyword,
                max_results=max_results_per_keyword,
                timeout=timeout
            )

            if result.get("success") and "results" in result:
                all_results.extend(result["results"])

            # 添加延迟，避免请求过快
            import asyncio
            await asyncio.sleep(2)

        return {
            "success": True,
            "platform": self.platform_config.name,
            "platform_display": self.platform_config.display_name,
            "keywords": keywords,
            "total_count": len(all_results),
            "results": all_results,
            "crawl_time": datetime.now().isoformat()
        }
