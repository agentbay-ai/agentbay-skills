#!/usr/bin/env python3
"""
将「爬取结果 JSON」与「情感结果 JSON」合并，输出符合报告生成要求的 processed JSON。
用于避免手写/粘贴时 content/title 中未转义双引号导致的 JSON 解析失败。

用法:
  python scripts/sentiment/write_processed.py --raw output/crawl.json --sentiment output/sentiment_only.json --output output/processed.json

情感结果 JSON 格式（--sentiment 文件）:
  {
    "results": [
      {"label": "正面", "score": 1.0, "confidence": 0.9},
      {"label": "中性", "score": 0.0, "confidence": 0.85},
      ...
    ],
    "agent_summary": "舆情总结正文...",
    "agent_recommendations": "建议1. ...\n2. ..."
  }
  results 长度须与爬取结果中的 results 一致、顺序一一对应。
"""
import argparse
import json
from pathlib import Path
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description="合并爬取结果与情感结果，输出 processed JSON（避免手写导致的双引号转义问题）"
    )
    parser.add_argument("--raw", "-r", required=True, help="爬取结果 JSON 文件路径")
    parser.add_argument("--sentiment", "-s", required=True, help="情感结果 JSON 文件路径（仅含 results + agent_summary + agent_recommendations）")
    parser.add_argument("--output", "-o", required=True, help="输出的 processed JSON 路径")
    args = parser.parse_args()

    with open(args.raw, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(args.sentiment, "r", encoding="utf-8") as f:
        sentiment_data = json.load(f)

    results = data.get("results", [])
    sentiment_list = sentiment_data.get("results", [])

    if len(sentiment_list) != len(results):
        raise SystemExit(
            f"错误：爬取结果共 {len(results)} 条，情感结果共 {len(sentiment_list)} 条，数量不一致。"
        )

    for i, item in enumerate(results):
        item["sentiment"] = sentiment_list[i]

    dist = {"正面": 0, "负面": 0, "中性": 0}
    total_score = 0.0
    for s in sentiment_list:
        label = s.get("label", "中性")
        dist[label] = dist.get(label, 0) + 1
        total_score += s.get("score", 0.0)

    n = len(results)
    data["sentiment_statistics"] = {
        "total_count": n,
        "sentiment_distribution": dist,
        "average_score": round(total_score / n, 3) if n else 0,
        "positive_ratio": round(dist.get("正面", 0) / n, 3) if n else 0,
        "negative_ratio": round(dist.get("负面", 0) / n, 3) if n else 0,
        "neutral_ratio": round(dist.get("中性", 0) / n, 3) if n else 0,
        "positive_count": dist.get("正面", 0),
        "negative_count": dist.get("负面", 0),
        "neutral_count": dist.get("中性", 0),
    }
    data["processed_time"] = datetime.now().isoformat()
    data["agent_summary"] = sentiment_data.get("agent_summary", "")
    data["agent_recommendations"] = sentiment_data.get("agent_recommendations", "")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已写入: {out_path}（共 {n} 条，可直接用于 report.py --input）")


if __name__ == "__main__":
    main()
