"""
PDF 导出模块
将舆情分析报告（Markdown）转为图文并茂的 PDF。
依赖：markdown、weasyprint（可选，缺失时仅跳过 PDF 生成）
中文显示：优先 reporter/fonts/（通用或按平台子目录 windows/mac/linux）→ 本机系统字体（按 OS 选择）→ 下载 WOFF → CDN woff2。
"""
from __future__ import annotations

import base64
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 用于 @font-face 的 CJK 字体族名，正文统一使用该字体
_CJK_FONT_FAMILY = "ReportCJK"

# 各平台系统 CJK 字体路径（路径, format），按优先级排列；Python 根据 sys.platform 选用
_SYSTEM_FONT_CANDIDATES: Dict[str, List[Tuple[Path, str]]] = {
    "darwin": [
        (Path("/System/Library/Fonts/PingFang.ttc"), "truetype"),
        (Path("/System/Library/Fonts/Supplemental/Songti.ttc"), "truetype"),
        (Path("/System/Library/Fonts/Supplemental/STHeiti Medium.ttc"), "truetype"),
        (Path("/Library/Fonts/Arial Unicode.ttf"), "truetype"),
    ],
    "win32": [
        (Path("C:/Windows/Fonts/msyh.ttc"), "truetype"),   # 微软雅黑
        (Path("C:/Windows/Fonts/simsun.ttc"), "truetype"), # 宋体
        (Path("C:/Windows/Fonts/simhei.ttf"), "truetype"), # 黑体
    ],
    "linux": [
        (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), "truetype"),
        (Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"), "truetype"),
        (Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"), "truetype"),
    ],
}
# 兼容 win64 等
if sys.platform == "win32":
    _PLATFORM_KEY = "win32"
elif sys.platform == "darwin":
    _PLATFORM_KEY = "darwin"
else:
    _PLATFORM_KEY = "linux"

# Markdown → HTML（必选）
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# HTML → PDF（可选，需系统安装 Pango/Cairo）
try:
    from weasyprint import HTML as WeasyHTML
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False


def _markdown_to_html(md_content: str) -> str:
    """将 Markdown 转为 HTML 片段（不含 document 包装）。"""
    if not MARKDOWN_AVAILABLE:
        raise RuntimeError("请安装 markdown: pip install markdown")
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"],
        extension_configs={"tables": {}},
    )
    return html_body


def _sentiment_chart_svg(stats: Dict[str, Any]) -> str:
    """根据情感统计生成简单 SVG 柱状图（图文并茂）。
    将「非常正面」合并入「正面」、「非常负面」合并入「负面」，与执行摘要比例一致。
    """
    total = stats.get("total_count", 0)
    if total <= 0:
        return ""

    dist = stats.get("sentiment_distribution", {})
    # 合并细粒度标签：正面=正面+非常正面，负面=负面+非常负面，其余归中性
    if any(k in dist for k in ("正面", "负面", "中性", "非常正面", "非常负面")):
        pos = dist.get("正面", 0) + dist.get("非常正面", 0)
        neg = dist.get("负面", 0) + dist.get("非常负面", 0)
        neu = total - pos - neg
        if neu < 0:
            neu = dist.get("中性", 0)
        labels_map = [
            ("正面", pos, "#22c55e"),
            ("负面", neg, "#ef4444"),
            ("中性", neu, "#94a3b8"),
        ]
    else:
        pos = dist.get("positive", 0)
        neg = dist.get("negative", 0)
        neu = total - pos - neg
        if neu < 0:
            neu = dist.get("neutral", 0)
        labels_map = [
            ("正面", pos, "#22c55e"),
            ("负面", neg, "#ef4444"),
            ("中性", neu, "#94a3b8"),
        ]

    max_count = max((c for _, c, _ in labels_map), default=1) or 1
    w, h = 400, 140
    bar_h = 24
    gap = 12
    margin = 40

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        f'<style>.bar-label{{font-family:{_CJK_FONT_FAMILY},sans-serif;font-size:12px;fill:#374151}}.bar-val{{font-family:{_CJK_FONT_FAMILY},sans-serif;font-size:11px;fill:#6b7280}}</style>',
    ]
    y = margin
    for label, count, color in labels_map:
        ratio = count / max_count
        bar_w = max(4, int(200 * ratio))
        parts.append(f'<rect x="{margin}" y="{y}" width="{bar_w}" height="{bar_h - 2}" rx="4" fill="{color}" opacity="0.85"/>')
        parts.append(f'<text class="bar-label" x="{margin}" y="{y + bar_h - 6}">{label}</text>')
        parts.append(f'<text class="bar-val" x="{margin + 210}" y="{y + bar_h - 6}">{count} ({100*count/total:.1f}%)</text>')
        y += bar_h + gap

    parts.append("</svg>")
    return "".join(parts)


def _font_path_to_file_url(path: Path) -> str:
    """将字体路径转为 WeasyPrint 可用的 file:// URL（含 Windows 盘符）。"""
    path = path.resolve()
    # Windows: file:///C:/Windows/Fonts/... ；Unix: file:///usr/share/...
    posix = path.as_posix()
    if posix.startswith("/"):
        return f"file://{posix}"
    return f"file:///{posix}"


def _get_cjk_font_css() -> str:
    """
    生成用于 PDF 的 CJK @font-face，避免中文乱码。
    优先级：1) reporter/fonts/ 通用字体 或 reporter/fonts/windows|mac|linux/ 按系统；
            2) 本机系统字体（按 Windows/macOS/Linux 选择）；
            3) 下载 Noto WOFF；4) CDN woff2。
    """
    report_dir = Path(__file__).resolve().parent
    fonts_dir = report_dir / "fonts"

    # 1a) 项目内 reporter/fonts/ 通用字体（任意 .ttf/.otf）
    if fonts_dir.is_dir():
        for name in ("NotoSansSC-Regular.otf", "NotoSansSC-Regular.ttf", "SourceHanSansSC-Regular.otf", "SimSun.ttf", "SimSun.otf"):
            path = fonts_dir / name
            if path.is_file():
                try:
                    data = path.read_bytes()
                    b64 = base64.b64encode(data).decode("ascii")
                    fmt = "opentype" if path.suffix.lower() == ".otf" else "truetype"
                    return f"""
        @font-face {{
            font-family: '{_CJK_FONT_FAMILY}';
            src: url(data:font/{fmt};base64,{b64}) format('{fmt}');
            font-weight: normal;
            font-style: normal;
        }}"""
                except Exception:
                    continue

    # 1b) 按系统使用 reporter/fonts/windows、reporter/fonts/mac、reporter/fonts/linux 下字体
    platform_subdir = {"win32": "windows", "darwin": "mac", "linux": "linux"}.get(_PLATFORM_KEY, "linux")
    platform_fonts_dir = fonts_dir / platform_subdir
    if platform_fonts_dir.is_dir():
        for ext in (".ttf", ".otf", ".ttc"):
            for path in sorted(platform_fonts_dir.glob(f"*{ext}")):
                if path.is_file():
                    try:
                        if path.suffix.lower() in (".ttf", ".otf"):
                            data = path.read_bytes()
                            b64 = base64.b64encode(data).decode("ascii")
                            fmt = "opentype" if path.suffix.lower() == ".otf" else "truetype"
                            return f"""
        @font-face {{
            font-family: '{_CJK_FONT_FAMILY}';
            src: url(data:font/{fmt};base64,{b64}) format('{fmt}');
            font-weight: normal;
            font-style: normal;
        }}"""
                        else:
                            url = _font_path_to_file_url(path)
                            return f"""
        @font-face {{
            font-family: '{_CJK_FONT_FAMILY}';
            src: url('{url}') format('truetype');
            font-weight: normal;
            font-style: normal;
        }}"""
                    except Exception:
                        continue

    # 2) 本机系统字体（按 Windows / macOS / Linux 选择）
    for path, fmt in _SYSTEM_FONT_CANDIDATES.get(_PLATFORM_KEY, []):
        if path.is_file():
            url = _font_path_to_file_url(path)
            return f"""
        @font-face {{
            font-family: '{_CJK_FONT_FAMILY}';
            src: url('{url}') format('{fmt}');
            font-weight: normal;
            font-style: normal;
        }}"""

    # 3) 下载 Noto Sans SC 到临时文件（CDN 仅有 woff/woff2；WeasyPrint 对远程 woff2 支持差）
    woff_url = (
        "https://cdn.jsdelivr.net/npm/@fontsource/noto-sans-sc@5.0.0/files/"
        "noto-sans-sc-5-400-normal.woff"
    )
    try:
        with tempfile.NamedTemporaryFile(suffix=".woff", delete=False) as f:
            req = urllib.request.Request(woff_url, headers={"User-Agent": "Mozilla/5.0 (compatible; WeasyPrint)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                f.write(resp.read())
            local_path = Path(f.name)
        return f"""
        @font-face {{
            font-family: '{_CJK_FONT_FAMILY}';
            src: url('file://{local_path}') format('woff');
            font-weight: normal;
            font-style: normal;
        }}"""
    except Exception:
        pass

    # 4) 最后回退：CDN woff2（WeasyPrint 可能无法正确加载，仅作兜底）
    woff2_url = (
        "https://cdn.jsdelivr.net/npm/@fontsource/noto-sans-sc@5.0.0/files/"
        "noto-sans-sc-5-400-normal.woff2"
    )
    return f"""
        @font-face {{
            font-family: '{_CJK_FONT_FAMILY}';
            src: url('{woff2_url}') format('woff2');
            font-weight: normal;
            font-style: normal;
        }}"""


def _wrap_html_document(html_body: str, title: str, chart_svg: str = "", cjk_font_css: str = "") -> str:
    """包装成完整 HTML 文档，带样式与可选图表。"""
    chart_block = ""
    if chart_svg:
        # 将 SVG 转为可嵌入的 data 或内联（避免外部依赖）
        chart_block = f"""
        <div class="chart-wrap">
            <h3>情感分布示意</h3>
            <div class="chart-inner">{chart_svg}</div>
        </div>
        """

    # 正文与图表统一使用 CJK 字体，避免乱码
    body_font = f"'{_CJK_FONT_FAMILY}', 'PingFang SC', 'Microsoft YaHei', 'SimSun', sans-serif"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8"/>
    <title>{_escape_html(title)}</title>
    <style>
        {cjk_font_css}
        @page {{ size: A4; margin: 2cm; }}
        body, h1, h2, h3, table, th, td, blockquote, ul, ol, .chart-wrap, .chart-inner {{ font-family: {body_font}; }}
        body {{ font-size: 12pt; line-height: 1.6; color: #1f2937; }}
        h1 {{ font-size: 18pt; color: #111; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; margin-top: 0; }}
        h2 {{ font-size: 14pt; color: #1e40af; margin-top: 1.2em; }}
        h3 {{ font-size: 12pt; color: #374151; margin-top: 1em; }}
        table {{ border-collapse: collapse; width: 100%; margin: 0.5em 0; font-size: 11pt; }}
        th, td {{ border: 1px solid #e5e7eb; padding: 6px 10px; text-align: left; }}
        th {{ background: #f3f4f6; font-weight: 600; }}
        blockquote {{ margin: 0.5em 0; padding: 0.5em 1em; background: #f9fafb; border-left: 4px solid #3b82f6; color: #4b5563; }}
        .chart-wrap {{ margin: 1em 0; padding: 1em; background: #f8fafc; border-radius: 8px; }}
        .chart-wrap h3 {{ margin-top: 0; }}
        .chart-inner {{ margin-top: 8px; }}
        ul, ol {{ margin: 0.4em 0; padding-left: 1.5em; }}
        strong {{ color: #111; }}
        hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 1em 0; }}
    </style>
</head>
<body>
    <h1>{_escape_html(title)}</h1>
    {chart_block}
    <div class="content">
    {html_body}
    </div>
</body>
</html>
"""


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def export_to_pdf(
    md_content: str,
    output_pdf_path: Path,
    title: str = "舆情分析报告",
    processed_results: Optional[Dict[str, Any]] = None,
    save_html: bool = True,
) -> Optional[Path]:
    """
    将 Markdown 报告内容导出为 PDF（图文并茂）。

    Args:
        md_content: 报告 Markdown 全文
        output_pdf_path: 输出 PDF 路径
        title: 报告标题，用于 HTML 标题与页眉
        processed_results: 可选，含 sentiment_statistics 时会在正文前插入情感分布图
        save_html: 是否同时保存中间生成的 HTML（与 PDF 同目录、同名 .html），默认 True

    Returns:
        成功时返回 output_pdf_path，依赖缺失或失败时返回 None
    """
    if not MARKDOWN_AVAILABLE:
        print("⚠ 未安装 markdown，无法生成 PDF。请运行: pip install markdown")
        return None

    html_body = _markdown_to_html(md_content)
    chart_svg = ""
    if processed_results:
        stats = processed_results.get("sentiment_statistics", {})
        if stats:
            chart_svg = _sentiment_chart_svg(stats)

    cjk_font_css = _get_cjk_font_css()
    full_html = _wrap_html_document(html_body, title, chart_svg, cjk_font_css=cjk_font_css)

    if not WEASYPRINT_AVAILABLE:
        print("⚠ 未安装或无法加载 weasyprint（需系统安装 Pango/Cairo），跳过 PDF 生成。")
        print("   macOS: brew install cairo pango gdk-pixbuf")
        print("   pip: pip install weasyprint")
        return None

    output_pdf_path = Path(output_pdf_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # 可选：保存中间生成的 HTML（与 PDF 同名 .html）
    if save_html:
        html_path = output_pdf_path.with_suffix(".html")
        try:
            html_path.write_text(full_html, encoding="utf-8")
            print(f"   HTML: {html_path}")
        except Exception as e:
            print(f"   HTML 保存跳过: {e}")

    try:
        font_config = FontConfiguration()
        doc = WeasyHTML(string=full_html, base_url=str(Path.cwd()))
        doc.write_pdf(
            output_pdf_path,
            font_config=font_config,
            presentational_hints=True,
        )
        return output_pdf_path
    except Exception as e:
        print(f"⚠ PDF 生成失败: {e}")
        return None


def is_pdf_available() -> bool:
    """是否具备 PDF 导出能力（markdown + weasyprint 均可用）。"""
    return bool(MARKDOWN_AVAILABLE and WEASYPRINT_AVAILABLE)
