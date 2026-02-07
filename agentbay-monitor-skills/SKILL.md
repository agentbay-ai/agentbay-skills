---
name: agentbay-monitor-skill
description: 舆情监控技能，最终产出舆情报告。爬取由本技能完成；情感分析由主 Agent 按提示词自主判断（无需传入 LLM 配置），结果写入指定路径；报告由本技能提供的 generate_report 生成。
dependencies:
  - wuying-agentbay-sdk
---

# AgentBay 舆情监控 Skill

## 何时使用

在以下场景下使用本技能：

- **中文**：舆情监控、舆情分析、情感分析、舆情报告、按关键词/平台做分析、多平台爬取与情感分析、生成舆情报告
- **English**：sentiment monitoring, sentiment analysis, public opinion report, crawl by keyword/platform, multi-platform sentiment

无需用户明确说「沙箱」或「AgentBay」；只要意图是舆情监控/分析/报告，即默认使用本技能。**本技能最终产出报告**：爬取 → 主 Agent 读取**指定路径的提示词文件**完成情感分析并将结果写入**指定路径** → 主 Agent 调用本技能的报告生成代码。

## 前置条件

- 工作目录为 **agentbay-monitor-skill** 技能目录（即本 SKILL 所在目录）
- 已安装依赖（见下方「依赖」）
- 已配置 `AGENTBAY_API_KEY`（见下方「API Key」）

## 依赖

本技能需安装以下 Python 包，使用前执行：

```bash
pip install wuying-agentbay-sdk pandas numpy pyyaml markdown
```

可选（生成 PDF 报告）：安装 weasyprint 及系统依赖（如 macOS：`brew install cairo pango gdk-pixbuf` 后 `pip install weasyprint`）。不装则仅跳过 PDF，不影响 .md/.json 报告。

## API Key 配置

**仅** `AGENTBAY_API_KEY` 需要配置，通过以下任一方式：

### 方式 1：环境变量（推荐）

在运行技能前设置环境变量：

**macOS/Linux**：
```bash
export AGENTBAY_API_KEY=你的key
```

**Windows (PowerShell)**：
```powershell
$env:AGENTBAY_API_KEY="你的key"
```

**Windows (CMD)**：
```cmd
set AGENTBAY_API_KEY=你的key
```

设置后，脚本会自动将环境变量写入配置文件 `~/.config/agentbay/api_key`（macOS/Linux）或 `%APPDATA%\agentbay\api_key`（Windows），后续可直接使用配置文件。

### 方式 2：配置文件

直接创建配置文件（无需设置环境变量）：

**macOS/Linux**：
```bash
mkdir -p ~/.config/agentbay
echo -n '你的key' > ~/.config/agentbay/api_key
```

**Windows**：
在 `%APPDATA%\agentbay\` 目录下创建 `api_key` 文件（无扩展名），内容为你的 API Key。

### 获取 API Key

访问 https://agentbay.console.aliyun.com/service-management 获取。

### 验证配置

运行任意脚本（如 `python scripts/crawl.py --keywords "test"`），若未配置会提示错误；若配置正确则正常执行。

**注意**：其余参数（平台、关键词、输出目录等）均由主 Agent 通过传参/命令行传入，无需环境变量。

## 整体流程（最终生成报告）

1. **爬取**：主 Agent 调用 `python scripts/crawl.py --keywords "..."` 或 `crawl_for_sentiment(...)`，得到 `crawl_results` 与 `raw_output_path`（JSON 文件路径）。
2. **情感分析（可定制提示词）**：主 Agent **从指定路径读取提示词文件**，按提示词对爬取结果做情感分析，**将结果写入指定路径的 JSON 文件**：
   - **提示词文件**（可定制）：默认 `scripts/sentiment/sentiment_instruction.md`，主 Agent 可读取用户指定的其它路径。
   - **输入**：爬取结果 JSON 文件路径（通常为 `raw_output_path` 或上一步保存的 crawl.json）。
   - **输出**：主 Agent 将符合格式的 `processed_results` JSON 写入指定路径（如 `output/processed.json`）。
   - 提示词文件中包含情感分析规则说明与**必须遵守的输出格式**，以便后续报告生成能正确读取。
3. **生成报告**：主 Agent 调用本技能提供的报告生成（读取上一步写入的结果文件）：
   - **脚本**：`python scripts/report.py --input <上一步写入的 JSON 路径> [--output-dir output] [--title "报告标题"]`
   - **代码**：`from crawl import generate_report; report = generate_report(processed_results, output_dir="output", title="...")`

最终产出：Markdown/JSON 报告（及可选 PDF）。

## 运行方式（传参）

**步骤 0：首次登录（仅非 Bing 平台需要）**

使用 **小红书、微博、抖音、知乎** 等平台时，**必须先完成登录**（Bing 搜索无需登录）：

```bash
python scripts/login.py --platform xhs [--context-name sentiment-analysis]
```

登录流程：
1. 程序打开浏览器流化页面
2. 用户在浏览器中完成登录操作（扫码或账号密码）
3. 登录完成后，在终端按 Enter 键
4. 登录状态会保存到 Browser Context，后续爬取自动使用

**注意**：不同平台需要使用不同的 `--context-name`，或分别登录。登录状态会持久化保存，除非手动删除 Context，否则不需要重复登录。

**步骤 1：爬取**

在 **agentbay-monitor-skill** 目录下：

```bash
python scripts/crawl.py --keywords "关键词1,关键词2" [--platform bing] [--output-dir output]
```

常用参数：`--keywords` / `-k`（必需）、`--platform` / `-p`（xhs/weibo/douyin/zhihu/bing，默认 bing）、`--max-results`、`--output-dir` / `-o`、`--report-title`、`--context-name`（需与登录时一致）、`--crawl-timeout`。

**Bing 爬取策略**：爬取 Bing 时**仅关注「资讯」板块**（新闻、报道等），且**不点击进入任何链接**（如千问官网、文章详情页），只在搜索结果列表页根据每条卡片的标题、摘要、链接直接提取，便于快速获取舆情摘要。

**注意**：使用非 Bing 平台（xhs/weibo/douyin/zhihu）时，必须确保已通过 `login.py` 完成登录，且 `--context-name` 与登录时一致。

**主 Agent 调用爬取时的超时与耗时（必读）**：

- **主 Agent 侧**：调用爬取脚本（命令行或 `crawl_for_sentiment`）时，**默认应将命令/调用的超时时间设为 10 分钟**（600 秒），否则爬取未完成就可能被中断。
- **耗时经验值**：一般**每爬取 1 条内容约消耗 1 分钟**（视平台与网络而定），可按「关键词数 × 每关键词最大条数」粗略估算所需时间。
- **脚本内超时（动态）**：脚本会**根据关键词数与每关键词最大结果数动态计算** `--crawl-timeout`。未显式传入 `--crawl-timeout` 时，公式为：**至少 10 分钟**，否则 **3 分钟基数 + 每条约 1 分钟**（即 `max(1200, 180 + 关键词数×每关键词最大条数×60)` 秒）。主 Agent 无需手动传 `--crawl-timeout`，除非需要更长或更短上限。

**步骤 2：情感分析（由主 Agent 自主完成，无需传入 LLM 配置）**

- 主 Agent 根据 `scripts/sentiment/sentiment_instruction.md` 中的规则**自主判断**每条内容的情感倾向，无需在技能中配置或传入任何 LLM API。
- 流程：主 Agent 读取提示词文件 → 读取爬取结果 JSON（如 `raw_output_path`）→ 按提示词逐条判定情感（正面/负面/中性及 score、confidence）→ 将结果按提示词规定的**输出格式**写入指定路径（如 `output/processed.json`）。

**步骤 3：生成报告（主 Agent 调用我们提供的代码）**

```bash
python scripts/report.py --input <步骤 2 写入的 JSON 路径> [--output-dir output] [--title "报告标题"]
```

## 输出与结果

- **爬取**：输出原始 JSON 文件路径（`raw_output_path`）及返回中的 `crawl_results`。
- **情感分析**：主 Agent 按**指定路径的提示词文件**完成分析，将结果写入**指定路径**的 JSON 文件；该文件须符合 `sentiment_instruction.md` 中规定的输出格式（含 `sentiment_statistics`、每条结果的 `sentiment`）。
- **报告**：主 Agent 调用 `generate_report`（或 `report.py`）读取上一步写入的 JSON，得到 `markdown_path`、`json_path`、可选 `pdf_path`。

## Agent 如何调用

- **登录**（仅非 Bing 平台需要）：使用 xhs/weibo/douyin/zhihu 前，主 Agent 应引导用户先运行 `python scripts/login.py --platform <平台>` 完成登录。Bing 平台跳过此步骤。
- **爬取**：`python scripts/crawl.py` 或 `crawl_for_sentiment(...)`，得到 `crawl_results`、`raw_output_path`（JSON 文件路径）。**主 Agent 调用时默认将命令/执行超时设为 10 分钟**；脚本内会按「约 1 条/分钟」动态计算 `--crawl-timeout`（不传即可）。使用非 Bing 平台时，确保 `context_name` 与登录时一致。
- **情感分析**：主 Agent **读取指定路径的提示词文件**（默认 `scripts/sentiment/sentiment_instruction.md`，可定制），从**输入路径**读取爬取 JSON，按提示词完成情感分析，**将结果写入指定路径**的 JSON 文件。
- **报告**：调用本技能提供的报告生成：`generate_report(processed_results, output_dir, title)` 或 `python scripts/report.py --input <上一步写入的 JSON 路径>`，得到报告文件路径。
- **失败**：未配置 `AGENTBAY_API_KEY`、未登录（非 Bing 平台）或爬取/分析失败时返回 `success: False` 及 `error`。

## 代码调用示例（完整流程）

主 Agent 可按以下顺序调用，最终生成报告。情感分析由主 Agent 按提示词完成并写文件。

```python
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from crawl import crawl_for_sentiment, generate_report

async def main():
    # 1. 爬取
    result = await crawl_for_sentiment(
        platform="bing",
        keywords=["产品名称", "品牌名"],
        max_results_per_keyword=50,
        output_dir="output",
        report_title="舆情分析",
    )
    if not result.get("success"):
        print("爬取失败:", result.get("error"))
        return
    raw_path = result.get("raw_output_path")  # 爬取结果 JSON 路径

    # 2. 情感分析：主 Agent 读取 scripts/sentiment/sentiment_instruction.md，
    #         按提示词对 raw_path 做分析，将结果写入 output/processed.json（格式见提示词）
    # 主 Agent 在此处：读取提示词文件 → 读取 raw_path → 完成情感分析 → 写入 processed_path
    processed_path = Path("output") / "processed.json"
    # ... 主 Agent 完成情感分析并写入 processed_path ...

    # 3. 生成报告（读取上一步写入的 JSON）
    with open(processed_path, "r", encoding="utf-8") as f:
        processed_results = json.load(f)
    report = generate_report(processed_results, output_dir="output", title="舆情分析报告")
    print("报告:", report.get("markdown_path"), report.get("pdf_path"))

if __name__ == "__main__":
    asyncio.run(main())
```

## 常见问题

- **情感分析谁来做**：由**主 Agent 自主完成**。主 Agent 读取 `scripts/sentiment/sentiment_instruction.md`，按其中规则对爬取结果逐条判断情感并写入 `processed.json`，**无需在技能中传入或配置 LLM**。
- **情感分析提示词**：默认路径 `scripts/sentiment/sentiment_instruction.md`，可编辑该文件定制规则；主 Agent 从**输入路径**读爬取 JSON，完成分析后写入**输出路径**。输出格式须遵守提示词中的规定，以便报告生成正常。
- **平台登录**：Bing 搜索无需登录；使用 xhs/weibo/douyin/zhihu 前必须先运行 `python scripts/login.py --platform <平台>` 完成登录。登录状态保存在 Browser Context 中，后续爬取自动使用。
- **登录状态失效**：重新执行 `python scripts/login.py --platform <平台> [--context-name ...]` 完成登录。
- **爬取超时**：脚本未传 `--crawl-timeout` 时会按「约 1 条/分钟」动态计算（至少 10 分钟）；主 Agent 调用爬取时**默认将命令超时设为 10 分钟**。若需更长可显式传 `--crawl-timeout`（秒）。

## 技能内文件结构

```
agentbay-monitor-skill/
├── SKILL.md             # 本技能说明
├── scripts/
│   ├── crawl.py         # crawl_for_sentiment / generate_report（爬取入口）
│   ├── report.py        # 报告生成脚本（主 Agent 调用）
│   ├── login.py         # 首次登录
│   ├── crawler/         # 爬取
│   ├── sentiment/       # 情感分析（提示词）
│   │   └── sentiment_instruction.md  # 主 Agent 用提示词（可定制），含输入/输出路径与输出格式
│   └── reporter/        # 报告生成实现（ReportGenerator 等）
└── output/              # 默认输出目录（爬取 JSON、情感结果 JSON、报告）
```
