"""
无影舆情爬取服务主入口
本技能仅负责按关键词/平台爬取原始数据并返回；情感分析、报告生成由主 Agent 完成。
除 AGENTBAY_API_KEY 外，其余参数由主 Agent 通过传参/命令行传入。
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# 从技能根目录运行 python scripts/crawl.py 时，将 scripts 加入 path 以便导入
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import asyncio
import argparse
import os
from typing import List, Optional, Dict, Any

from crawler import SocialMediaCrawler, get_platform_config, create_crawler_session
from reporter import ReportGenerator


def get_api_key():
    """从 ~/.config/agentbay/api_key 或环境变量 AGENTBAY_API_KEY 获取 API Key"""
    from pathlib import Path
    file_path = Path.home() / ".config" / "agentbay" / "api_key"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.touch()
    if os.environ.get("AGENTBAY_API_KEY"):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(os.environ.get("AGENTBAY_API_KEY"))
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
        if not api_key:
            api_key = None
    except Exception as e:
        api_key = None
    return api_key


# ---------- 以下供主 Agent 在爬取完成后调用：报告生成 ----------


def generate_report(
    processed_results: Dict[str, Any],
    output_dir: str = "output",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    根据情感分析结果生成报告（Markdown/JSON/可选 PDF），供主 Agent 调用。

    Args:
        processed_results: 主 Agent 按提示词完成情感分析后写入的 JSON（需符合 sentiment_instruction.md 中的输出格式）
        output_dir: 报告输出目录
        title: 报告标题，可选

    Returns:
        含 markdown_path、json_path、pdf_path（若有）等的字典
    """
    generator = ReportGenerator(output_dir=output_dir)
    return generator.generate_report(processed_results=processed_results, title=title)


def _compute_crawl_timeout(keywords: List[str], max_results_per_keyword: int) -> int:
    """按「约 1 条/分钟」动态计算爬取超时（秒），至少 10 分钟。"""
    total_max = len(keywords) * max_results_per_keyword
    return max(1200, 180 + total_max * 60)


async def crawl_for_sentiment(
    platform: str,
    keywords: List[str],
    *,
    max_results_per_keyword: int = 10,
    output_dir: Optional[str] = None,
    report_title: Optional[str] = None,
    agentbay_api_key: Optional[str] = None,
    context_name: str = "sentiment-analysis",
    crawl_timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    按关键词/平台爬取原始数据并返回。不在此做情感分析或报告生成，由主 Agent 基于返回数据完成。

    Args:
        platform: 平台标识（"xhs", "weibo", "bing" 等）
        keywords: 关键词列表
        max_results_per_keyword: 每个关键词的最大结果数
        output_dir: 原始数据输出目录，默认 "output"
        report_title: 用于生成输出文件名，可选
        agentbay_api_key: AgentBay API Key，未传则从环境变量 AGENTBAY_API_KEY 读取
        context_name: Browser Context 名称
        crawl_timeout: 爬取超时（秒）；不传或为 None 时按「约 1 条/分钟」动态计算，至少 10 分钟

    Returns:
        含 success、crawl_results、raw_output_path（可选）的字典
    """
    if crawl_timeout is None or crawl_timeout <= 0:
        crawl_timeout = _compute_crawl_timeout(keywords, max_results_per_keyword)
        print(f"⏱️ 爬取超时已动态设置为 {crawl_timeout} 秒（约 1 条/分钟，至少 10 分钟）\n")

    api_key = (agentbay_api_key or "").strip() or get_api_key()
    if not api_key:
        return {
            "success": False,
            "error": "未提供 AGENTBAY_API_KEY（请设置环境变量 AGENTBAY_API_KEY 或创建 ~/.config/agentbay/api_key 文件）",
        }

    if not keywords:
        return {"success": False, "error": "关键词 keywords 不能为空"}

    out_dir = output_dir or "output"

    print(f"\n{'='*60}")
    print(f"🚀 启动舆情爬取（情感分析由主 Agent 完成）")
    print(f"{'='*60}\n")

    try:
        platform_config = get_platform_config(platform)
        print(f"📱 目标平台: {platform_config.display_name}")
    except ValueError as e:
        return {"success": False, "error": str(e)}

    print(f"🔍 关键词: {', '.join(keywords)}")
    print(f"📊 每个关键词最大结果数: {max_results_per_keyword}\n")

    adapter = None
    try:
        print("=" * 60)
        print("步骤1: 创建爬取会话")
        print("=" * 60)
        adapter = await create_crawler_session(
            api_key=api_key,
            context_name=context_name,
            platform_config=platform_config,
        )

        print("\n" + "=" * 60)
        print("步骤2: 执行内容爬取")
        print("=" * 60)
        crawler = SocialMediaCrawler(adapter, platform_config)

        if len(keywords) == 1:
            crawl_results = await crawler.crawl_by_keyword(
                keyword=keywords[0],
                max_results=max_results_per_keyword,
                timeout=crawl_timeout,
            )
        else:
            crawl_results = await crawler.crawl_multiple_keywords(
                keywords=keywords,
                max_results_per_keyword=max_results_per_keyword,
                timeout=crawl_timeout,
            )

        if not crawl_results.get("success"):
            return crawl_results

        crawl_results["data_sources"] = [crawl_results.get("platform_display", "浏览器爬取")]

        # 将原始爬取结果写入 output_dir，供主 Agent 做情感分析/报告
        raw_output_path = None
        try:
            out_path = Path(out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            platform_display = crawl_results.get("platform_display", platform)
            title_part = (report_title or f"{platform_display}_{','.join(keywords[:2])}").replace(" ", "_")[:50]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_filename = f"{platform}_{title_part}_{ts}.json"
            raw_output_path = out_path / raw_filename
            with open(raw_output_path, "w", encoding="utf-8") as f:
                json.dump(crawl_results, f, ensure_ascii=False, indent=2)
            raw_output_path = str(raw_output_path)
        except Exception as e:
            print(f"   ⚠️ 写入原始数据文件失败（不影响返回）: {e}")

        print("\n" + "=" * 60)
        print("✅ 爬取完成，原始数据已返回（情感分析由主 Agent 完成）")
        print("=" * 60)

        return {
            "success": True,
            "crawl_results": crawl_results,
            "raw_output_path": raw_output_path,
        }

    except Exception as e:
        import traceback
        error_msg = f"爬取过程中发生错误: {str(e)}"
        print(f"\n❌ {error_msg}")
        print(f"详细错误:\n{traceback.format_exc()}")
        return {"success": False, "error": error_msg}

    finally:
        if adapter:
            await adapter.close()


def _parse_args():
    parser = argparse.ArgumentParser(
        description="舆情爬取：除 AGENTBAY_API_KEY 外，其余参数由主 Agent 传入；情感分析由主 Agent 完成。",
    )
    parser.add_argument("--keywords", "-k", required=True, help="关键词，多个用逗号分隔")
    parser.add_argument("--platform", "-p", default="baidu", help="平台: baidu/xhs/weibo/douyin/zhihu/bing（默认 baidu）")
    parser.add_argument("--max-results", type=int, default=10, help="每关键词最大结果数（默认10）")
    parser.add_argument("--output-dir", "-o", default="output", help="报告输出目录")
    parser.add_argument("--report-title", help="报告标题（可选）")
    parser.add_argument("--context-name", default="sentiment-analysis", help="Browser Context 名称")
    parser.add_argument(
        "--crawl-timeout",
        type=int,
        default=None,
        help="爬取超时（秒）；不传时按「约 1 条/分钟」动态计算，至少 10 分钟",
    )
    return parser.parse_args()


async def main():
    args = _parse_args()
    keywords = [kw.strip() for kw in args.keywords.split(",") if kw.strip()]
    if not keywords:
        print("❌ 错误: --keywords 不能为空")
        sys.exit(1)

    # 未传 --crawl-timeout 时由 crawl_for_sentiment 内部按「约 1 条/分钟」动态计算
    effective_timeout = args.crawl_timeout
    if effective_timeout is None:
        effective_timeout = _compute_crawl_timeout(keywords, args.max_results)
    print(f"\n📋 参数: 平台={args.platform}, 关键词={', '.join(keywords)}, 每关键词最大={args.max_results}, 输出={args.output_dir}, 爬取超时={effective_timeout} 秒")
    if args.report_title:
        print(f"   报告标题: {args.report_title}")
    print()

    result = await crawl_for_sentiment(
        platform=args.platform,
        keywords=keywords,
        max_results_per_keyword=args.max_results,
        output_dir=args.output_dir,
        report_title=args.report_title or None,
        context_name=args.context_name,
        crawl_timeout=args.crawl_timeout,
    )

    if result.get("success"):
        print("\n✅ 爬取完成！")
        path = result.get("raw_output_path")
        if path:
            print(f"📄 原始数据: {path}")
        print("   情感分析、报告由主 Agent 基于返回数据完成。")
    else:
        print(f"\n❌ 爬取失败: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
