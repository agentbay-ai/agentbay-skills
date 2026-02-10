#!/usr/bin/env python3
"""
根据情感分析结果生成报告（Markdown/JSON/可选 PDF），供主 Agent 在情感分析完成后调用。
用法：python scripts/report.py --input processed.json [--output-dir output] [--title "报告标题"]
"""
import sys
import json
import argparse
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from crawl import generate_report


def main():
    parser = argparse.ArgumentParser(description="根据情感分析结果生成舆情报告")
    parser.add_argument("--input", "-i", required=True, help="processed 结果 JSON 文件路径（主 Agent 按提示词完成情感分析后写入）")
    parser.add_argument("--output-dir", "-o", default="output", help="报告输出目录")
    parser.add_argument("--title", "-t", help="报告标题，可选")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            processed_results = json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(
            f"输入 JSON 解析失败（{e.msg}，约第 {e.lineno} 行第 {e.colno} 列）。\n"
            "常见原因：内容字段（如 title、content）中含有未转义的双引号 \"。\n"
            "解决：请用程序生成 processed 文件（如 Python：先 json.load 爬取结果，添加 sentiment 后用 json.dump 写入），勿手写或直接粘贴含引号的内容。"
        )

    report = generate_report(
        processed_results=processed_results,
        output_dir=args.output_dir,
        title=args.title,
    )
    print(f"Markdown: {report.get('markdown_path', '')}")
    if report.get("json_path"):
        print(f"JSON: {report['json_path']}")
    if report.get("pdf_path"):
        print(f"PDF: {report['pdf_path']}")


if __name__ == "__main__":
    main()
