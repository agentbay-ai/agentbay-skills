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

    with open(args.input, "r", encoding="utf-8") as f:
        processed_results = json.load(f)

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
