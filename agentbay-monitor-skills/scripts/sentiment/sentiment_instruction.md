# 情感分析任务说明（主 Agent 用）

主 Agent 请按本提示词完成情感分析：**从指定路径读取爬取结果 JSON，对每条内容做情感判定，将结果写入指定路径的 JSON 文件**。本文件可定制，修改后主 Agent 将按新提示执行。

---

## 1. 输入

- **爬取结果文件路径**：由主 Agent 或调用方传入（通常为 `crawl_for_sentiment` 返回的 `raw_output_path`，或 `--input` 指定路径）。
- 文件内容为爬取结果 JSON，结构包含：
  - `success`: true
  - `results`: 数组，每项至少含 `content` 或 `title`（待分析文本）、以及其它爬取字段
  - `platform_display`、`keyword`/`keywords`、`data_sources` 等元信息

---

## 2. 情感分析规则（可在此定制）

请对 `results` 中每条内容，根据其 `content` 或 `title` 的文本，判定情感并赋予：

- **标签** `label`：取值为 **「正面」**、**「负面」**、**「中性」** 之一。
- **分数** `score`：数字，建议正面=1.0，负面=-1.0，中性=0.0（若需更细粒度可沿用 -2～2）。
- **置信度** `confidence`：0～1 的浮点数，表示判定置信度。

**规则建议（可编辑本段定制）**：

- 正面：表扬、认可、推荐、满意、感谢等倾向。
- 负面：批评、投诉、失望、反对、贬损等倾向。
- 中性：客观陈述、无明显情感倾向、或正负兼有难以判断。

主 Agent 可使用自身能力（如 LLM）按上述规则对每条文本进行判定；也可采用关键词规则等，只要输出符合下方「输出格式」即可。

---

## 3. 输出格式（必须严格遵守）

主 Agent 将分析结果写入 **指定路径** 的 JSON 文件。该 JSON 必须与下述结构兼容，以便后续 `generate_report` 能正确生成报告。

### 3.1 整体结构

- 保留爬取结果中的原有字段（如 `success`、`platform_display`、`keyword`/`keywords`、`data_sources`、`platform` 等）。
- 必须包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 固定为 true |
| `results` | array | 与输入同序，每项在原有基础上增加 `sentiment` 对象 |
| `sentiment_statistics` | object | 见下表 |
| `processed_time` | string | 可选，ISO 时间字符串 |

### 3.2 每条 `results[i]` 的 `sentiment` 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `label` | string | 仅限 "正面"、"负面"、"中性" 之一 |
| `score` | number | 建议 1.0 / -1.0 / 0.0 |
| `confidence` | number | 0～1 |

### 3.3 `sentiment_statistics` 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_count` | number | results 条数 |
| `sentiment_distribution` | object | 各 label 的数量，如 `{"正面": 10, "负面": 2, "中性": 5}` |
| `average_score` | number | 所有 score 的算术平均，保留 3 位小数 |
| `positive_ratio` | number | 正面条数/总条数，0～1，保留 3 位小数 |
| `negative_ratio` | number | 负面条数/总条数，0～1，保留 3 位小数 |
| `neutral_ratio` | number | 中性条数/总条数，0～1，保留 3 位小数 |
| `positive_count` | number | 正面条数 |
| `negative_count` | number | 负面条数 |
| `neutral_count` | number | 中性条数 |

### 3.4 主 Agent 撰写的总结与建议（报告「结论与建议」章节用）

主 Agent 在完成逐条情感判定后，**必须**根据情感分布与内容要点，撰写两段文字并写入同一 JSON，以便报告生成时直接使用，避免报告里结论与建议过于单薄。

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_summary` | string | **舆情总结**：一段或数段话，归纳本次舆情整体倾向、情感分布、内容中的主要观点或争议点（如活动反响、用户反馈、媒体报道侧重等）。不要只写一句「整体舆情偏向正面/中性/负面」，需结合具体话题与数据展开，约 100～300 字。 |
| `agent_recommendations` | string | **应对建议**：多条可执行建议，用编号列表（如 1. 2. 3.）或分段书写。内容需结合情感结果与内容要点（如正面多则如何放大、有负面则如何应对、中性多则如何引导等），不要只写一句泛泛建议。约 80～200 字。 |

---

## 4. 如何写入输出（必读，避免 JSON 解析失败）

**必须用本技能提供的合并脚本生成 processed JSON，不要手写或把整段内容粘贴进文件。**

爬取结果里的 `title`、`content` 等字段常含英文双引号 `"`（如 `"人间值得"`）。若手写或粘贴进 JSON，这些引号未转义会导致 `report.py` 报错 `JSONDecodeError: Expecting ',' delimiter`。

**正确做法：**

1. 主 Agent 只产出「情感结果」：对每条内容判定后，将结果写成一份**小 JSON**（仅含每条 label/score/confidence + agent_summary + agent_recommendations，不包含原始 content/title）。
2. 运行本目录下的合并脚本，生成最终 processed 文件：

```bash
python scripts/sentiment/write_processed.py --raw <爬取结果路径> --sentiment <情感结果JSON路径> --output <输出路径>
```

脚本会合并爬取数据与情感结果并用程序写入，自动处理转义。情感结果 JSON 格式见下方。

**情感结果 JSON 格式（--sentiment 文件）：**

```json
{
  "results": [
    {"label": "正面", "score": 1.0, "confidence": 0.9},
    {"label": "中性", "score": 0.0, "confidence": 0.85}
  ],
  "agent_summary": "舆情总结正文...",
  "agent_recommendations": "建议1. ...\n2. ..."
}
```

`results` 长度与顺序须与爬取结果中的 `results` 一致、一一对应。更多说明可运行 `python scripts/sentiment/write_processed.py --help`。

---

## 5. 输出路径

- **情感结果小 JSON**：主 Agent 写入到约定路径（如 `output/sentiment_only.json`），供 `write_processed.py --sentiment` 使用。
- **processed 文件路径**：由 `write_processed.py --output` 指定；生成后由主 Agent 调用 `generate_report --input <该路径>` 生成报告。

---

## 6. 流程小结

1. 主 Agent 读取 **本提示词文件**（默认路径：`scripts/sentiment/sentiment_instruction.md`，或调用方指定的路径）。
2. 主 Agent 从 **输入路径** 读取爬取结果 JSON。
3. 主 Agent 按本提示词中的「情感分析规则」对每条内容进行判定。
4. 主 Agent 根据情感分布与内容要点撰写 **舆情总结**（`agent_summary`）与 **应对建议**（`agent_recommendations`）。
5. 主 Agent 将「情感结果」（每条 sentiment + agent_summary + agent_recommendations）按上文格式写成一份小 JSON，保存到指定路径（如 `output/sentiment_only.json`）。
6. 主 Agent 运行 `python scripts/sentiment/write_processed.py --raw <爬取结果路径> --sentiment <上一步情感结果JSON> --output <processed 路径>`，得到最终 processed 文件。
7. 主 Agent 调用 `generate_report --input <processed 路径>` 生成报告；报告中的「结论与建议」将使用情感结果中的 `agent_summary` 与 `agent_recommendations`。

**定制说明**：编辑本文件中「情感分析规则」等段落即可改变主 Agent 的判定方式；输出格式请勿修改，以保证报告生成正常。
