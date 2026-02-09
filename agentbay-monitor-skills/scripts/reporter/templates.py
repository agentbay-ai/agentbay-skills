"""
报告模板
定义报告格式和结构
"""
from typing import Dict, Any, List


class ReportTemplate:
    """报告模板类"""

    @staticmethod
    def get_default_template() -> str:
        """获取默认报告模板"""
        return """# 【舆情分析报告】{title}

## 执行摘要

### 核心舆情发现
- **主要情感倾向**: {sentiment_summary}
- **关键数据指标**:
  - 总内容数: {total_count}
  - 正面比例: {positive_ratio}%
  - 负面比例: {negative_ratio}%
  - 中性比例: {neutral_ratio}%
  - 平均情感分数: {average_score}

### 平台分布概览
{platform_summary}

## 一、数据概览

### 1.1 数据来源统计
{data_source_table}

### 1.2 情感分布详情
{sentiment_distribution_table}

### 1.3 时间分布分析
{time_distribution}

## 二、舆情内容分析

### 2.1 正面声音
{positive_content}

### 2.2 负面声音
{negative_content}

### 2.3 中性观点
{neutral_content}

## 三、深度洞察

### 3.1 舆情趋势分析
{trend_analysis}

### 3.2 关键话题识别
{key_topics}

### 3.3 用户参与度分析
{engagement_analysis}

## 四、结论与建议

### 4.1 舆情总结
{conclusion}

### 4.2 应对建议
{recommendations}

## 数据附录

### 关键数据汇总
{data_appendix}

### 原始数据统计
{raw_data_stats}

---
*报告生成时间: {report_time}*
*数据来源: {data_sources}*
"""

    @staticmethod
    def format_sentiment_summary(stats: Dict[str, Any]) -> str:
        """格式化情感摘要"""
        avg_score = stats.get("average_score", 0.0)
        if avg_score > 0.5:
            return "整体偏向正面 😊"
        elif avg_score < -0.5:
            return "整体偏向负面 😞"
        else:
            return "整体偏向中性 😐"

    @staticmethod
    def format_platform_summary(results: Dict[str, Any]) -> str:
        """格式化平台摘要"""
        data_sources = results.get("data_sources")
        if data_sources and isinstance(data_sources, list):
            sources_str = "、".join(data_sources)
        else:
            sources_str = results.get("platform_display", "未知平台")
        total = results.get("total_count", 0)
        return f"- **数据来源**: {sources_str}\n- **总条数**: {total} 条"

    @staticmethod
    def format_data_source_table(results: Dict[str, Any]) -> str:
        """格式化数据来源表格"""
        data_sources = results.get("data_sources")
        if data_sources and isinstance(data_sources, list):
            platform = "、".join(data_sources)
        else:
            platform = results.get("platform_display", "未知平台")
        total = results.get("total_count", 0)
        keyword = results.get("keyword", "") or ", ".join(results.get("keywords", []))

        return f"""| 平台/来源 | 关键词 | 内容数量 |
|----------|--------|----------|
| {platform} | {keyword} | {total} |"""

    @staticmethod
    def format_sentiment_distribution_table(stats: Dict[str, Any]) -> str:
        """格式化情感分布表格"""
        dist = stats.get("sentiment_distribution", {})

        table = """| 情感类型 | 数量 | 比例 |
|----------|------|------|"""

        total = stats.get("total_count", 0)
        for label, count in dist.items():
            ratio = (count / total * 100) if total > 0 else 0
            table += f"\n| {label} | {count} | {ratio:.1f}% |"

        return table

    @staticmethod
    def format_content_section(
        results: List[Dict[str, Any]],
        sentiment_type: str,
        max_items: int = 5
    ) -> str:
        """格式化内容部分"""
        # 筛选指定情感类型的内容
        filtered = [
            item for item in results
            if item.get("sentiment", {}).get("label", "") == sentiment_type
        ]

        if not filtered:
            return f"暂无{sentiment_type}内容。"

        # 按置信度排序，取前N条
        filtered.sort(
            key=lambda x: x.get("sentiment", {}).get("confidence", 0),
            reverse=True
        )

        # 舆情内容预览：每条显示约 500 字，便于报告可读；联网搜索摘要保留全文
        max_preview_chars = 500
        content = ""
        for i, item in enumerate(filtered[:max_items], 1):
            title = item.get("title", "无标题")
            author = item.get("author") or item.get("source") or "未知作者"
            raw_text = item.get("content", "")
            # 联网搜索条目通常为完整摘要，保留全文；其它来源做预览截断
            if item.get("source") == "web_search":
                text = raw_text
                suffix = ""
            else:
                text = raw_text[:max_preview_chars] if len(raw_text) > max_preview_chars else raw_text
                suffix = "..." if len(raw_text) > max_preview_chars else ""
            confidence = item.get("sentiment", {}).get("confidence", 0)

            content += f"""
**{i}. {title}** —— @{author} (置信度: {confidence:.2f})
> {text}{suffix}
"""

        return content
