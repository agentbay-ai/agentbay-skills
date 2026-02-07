"""
报告生成器
生成舆情分析报告
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .templates import ReportTemplate


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = "output"):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.template = ReportTemplate()

    def generate_report(
        self,
        processed_results: Dict[str, Any],
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成舆情分析报告

        Args:
            processed_results: 处理后的舆情数据
            title: 报告标题，如果为None则自动生成

        Returns:
            包含报告内容和文件路径的字典
        """
        # 生成报告标题
        if title is None:
            platform = processed_results.get("platform_display", "未知平台")
            keyword = processed_results.get("keyword", "") or ", ".join(
                processed_results.get("keywords", [])
            )
            title = f"{platform} - {keyword} 舆情分析"

        # 获取统计数据
        stats = processed_results.get("sentiment_statistics", {})
        results = processed_results.get("results", [])

        # 格式化报告内容
        report_content = self.template.get_default_template().format(
            title=title,
            sentiment_summary=self.template.format_sentiment_summary(stats),
            total_count=stats.get("total_count", 0),
            positive_ratio=stats.get("positive_ratio", 0) * 100,
            negative_ratio=stats.get("negative_ratio", 0) * 100,
            neutral_ratio=stats.get("neutral_ratio", 0) * 100,
            average_score=stats.get("average_score", 0.0),
            platform_summary=self.template.format_platform_summary(processed_results),
            data_source_table=self.template.format_data_source_table(processed_results),
            sentiment_distribution_table=self.template.format_sentiment_distribution_table(stats),
            time_distribution=self._format_time_distribution(results),
            positive_content=self.template.format_content_section(results, "正面"),
            negative_content=self.template.format_content_section(results, "负面"),
            neutral_content=self.template.format_content_section(results, "中性"),
            trend_analysis=self._format_trend_analysis(stats),
            key_topics=self._format_key_topics(results),
            engagement_analysis=self._format_engagement_analysis(results),
            conclusion=self._format_conclusion(processed_results, stats),
            recommendations=self._format_recommendations(processed_results, stats),
            data_appendix=self._format_data_appendix(stats),
            raw_data_stats=self._format_raw_data_stats(processed_results),
            report_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data_sources=", ".join(processed_results.get("data_sources", [processed_results.get("platform_display", "未知平台")]))
        )

        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = processed_results.get("platform", "unknown")
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))[:50]
        filename = f"{platform}_{safe_title}_{timestamp}.md"
        filepath = self.output_dir / filename

        # 保存Markdown报告
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)

        # 保存JSON数据
        json_filename = filename.replace(".md", ".json")
        json_filepath = self.output_dir / json_filename
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(processed_results, f, ensure_ascii=False, indent=2)

        # 尝试生成 PDF（图文并茂）
        pdf_path = None
        try:
            from .pdf_export import export_to_pdf, is_pdf_available
            if is_pdf_available():
                pdf_filename = filename.replace(".md", ".pdf")
                pdf_filepath = self.output_dir / pdf_filename
                pdf_path = export_to_pdf(
                    report_content,
                    pdf_filepath,
                    title=title,
                    processed_results=processed_results,
                )
                if pdf_path:
                    print(f"   PDF: {pdf_path}")
        except Exception as e:
            print(f"   PDF 生成跳过: {e}")

        print(f"✅ 报告已生成:")
        print(f"   Markdown: {filepath}")
        print(f"   JSON数据: {json_filepath}")

        result = {
            "success": True,
            "title": title,
            "markdown_path": str(filepath),
            "json_path": str(json_filepath),
            "content": report_content,
            "statistics": stats
        }
        if pdf_path:
            result["pdf_path"] = str(pdf_path)
            result["html_path"] = str(Path(pdf_path).with_suffix(".html"))
        return result

    def _format_time_distribution(self, results: List[Dict[str, Any]]) -> str:
        """格式化时间分布"""
        if not results:
            return "暂无时间数据。"

        # 简单的时间分布统计
        return f"共收集 {len(results)} 条内容，时间范围: 待分析"

    def _format_trend_analysis(self, stats: Dict[str, Any]) -> str:
        """格式化趋势分析"""
        avg_score = stats.get("average_score", 0.0)
        positive_ratio = stats.get("positive_ratio", 0.0)
        negative_ratio = stats.get("negative_ratio", 0.0)

        if avg_score > 0.3:
            trend = "整体舆情趋势偏向正面，用户反馈较为积极。"
        elif avg_score < -0.3:
            trend = "整体舆情趋势偏向负面，需要关注用户反馈中的问题。"
        else:
            trend = "整体舆情趋势较为中性，用户反馈相对平衡。"

        return f"""
根据情感分析结果：
- 平均情感分数: {avg_score:.2f}
- 正面内容占比: {positive_ratio*100:.1f}%
- 负面内容占比: {negative_ratio*100:.1f}%

{trend}
"""

    def _format_key_topics(self, results: List[Dict[str, Any]]) -> str:
        """格式化关键话题"""
        if not results:
            return "暂无话题数据。"

        # 简单提取标题作为话题
        topics = [item.get("title", "") for item in results[:10] if item.get("title")]
        if topics:
            topics_str = "\n".join([f"- {topic}" for topic in topics[:5]])
            return f"主要话题包括：\n{topics_str}"
        else:
            return "暂无话题数据。"

    def _format_engagement_analysis(self, results: List[Dict[str, Any]]) -> str:
        """格式化参与度分析"""
        if not results:
            return "暂无参与度数据。"

        # 统计点赞、转发、评论
        total_likes = sum(item.get("likes", 0) or 0 for item in results)
        total_shares = sum(item.get("shares", 0) or 0 for item in results)
        total_comments = sum(item.get("comments", 0) or 0 for item in results)

        return f"""
- 总点赞数: {total_likes}
- 总转发数: {total_shares}
- 总评论数: {total_comments}
- 平均互动数: {(total_likes + total_shares + total_comments) / len(results):.1f}
"""

    def _format_conclusion(
        self, processed_results: Dict[str, Any], stats: Dict[str, Any]
    ) -> str:
        """格式化结论：优先使用主 Agent 撰写的 agent_summary，否则回退到基于统计的简短结论"""
        agent_summary = processed_results.get("agent_summary") or ""
        if agent_summary and agent_summary.strip():
            return agent_summary.strip()
        avg_score = stats.get("average_score", 0.0)
        total = stats.get("total_count", 0)
        if avg_score > 0.3:
            return f"整体舆情偏向正面，共分析 {total} 条内容，用户反馈积极。"
        if avg_score < -0.3:
            return f"整体舆情偏向负面，共分析 {total} 条内容，需要关注用户反馈中的问题。"
        return f"整体舆情较为中性，共分析 {total} 条内容，用户反馈相对平衡。"

    def _format_recommendations(
        self, processed_results: Dict[str, Any], stats: Dict[str, Any]
    ) -> str:
        """格式化建议：优先使用主 Agent 撰写的 agent_recommendations，否则回退到基于统计的简短建议"""
        agent_rec = processed_results.get("agent_recommendations") or ""
        if agent_rec and agent_rec.strip():
            return agent_rec.strip()
        avg_score = stats.get("average_score", 0.0)
        negative_ratio = stats.get("negative_ratio", 0.0)
        recommendations = []
        if negative_ratio > 0.3:
            recommendations.append("负面反馈占比较高，建议重点关注并采取应对措施。")
        if avg_score < -0.3:
            recommendations.append("整体情感偏向负面，建议加强用户沟通和服务改进。")
        elif avg_score > 0.3:
            recommendations.append("整体情感偏向正面，建议继续保持并放大正面影响。")
        if not recommendations:
            recommendations.append("舆情状况良好，建议持续监测。")
        return "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])

    def _format_data_appendix(self, stats: Dict[str, Any]) -> str:
        """格式化数据附录"""
        return f"""
- 总内容数: {stats.get('total_count', 0)}
- 正面内容: {stats.get('positive_count', 0)}
- 负面内容: {stats.get('negative_count', 0)}
- 中性内容: {stats.get('neutral_count', 0)}
- 平均情感分数: {stats.get('average_score', 0.0):.3f}
"""

    def _format_raw_data_stats(self, processed_results: Dict[str, Any]) -> str:
        """格式化原始数据统计"""
        platform = processed_results.get("platform_display", "未知平台")
        keyword = processed_results.get("keyword", "") or ", ".join(
            processed_results.get("keywords", [])
        )
        crawl_time = processed_results.get("crawl_time", "")
        processed_time = processed_results.get("processed_time", "")

        return f"""
- 数据来源平台: {platform}
- 搜索关键词: {keyword}
- 爬取时间: {crawl_time}
- 处理时间: {processed_time}
"""
