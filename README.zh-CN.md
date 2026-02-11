# AgentBay Skills

[English](./README.md) | **中文**

[AgentBay](https://github.com/agentbay-ai) 的技能集合，支持在沙箱中运行代码、浏览器自动化、舆情监控、股票分析、图像生成并与外部服务集成。

## 包含内容

| 技能 | 说明 |
|------|------|
| agentbay-aio-skills | 在 AgentBay 沙箱中运行代码（Python、JavaScript、R、Java）。由「run this code」「帮我跑一下这段代码」等触发，无需说「沙箱」。 |
| agentbay-monitor-skills | 舆情监控：爬取 → 情感分析 → 生成报告（Markdown/PDF）。由「舆情分析」「舆情报告」等触发。 |
| amap-traffic | 高德地图实时路况与最优自驾路线规划。需配置 `AMAP_KEY`。 |
| boss-job-search | 查询 Boss 直聘职位信息，支持职位、公司规模等筛选。 |
| china-stock-analysis | A 股价值投资分析：选股、个股深度分析、行业对比与估值计算，使用 akshare 获取财务数据。 |
| douban-movie-review | 查询豆瓣电影影评、评分与热门短评。 |
| find-skills | 在技能市场中搜索、发现与安装 Agent 技能。触发词如「查找插件」「搜索技能」「install skill」「find a skill for X」等。 |
| im-reminder | IM 定时提醒（一次性与周期），基于 cron 在指定时间送达原频道（飞书、webchat）。 |
| moltbook-hot-posts | 查询 Moltbook（Agent 社区）热帖与讨论。 |
| qwen-image | 通过通义万相（Qwen Image API）生成图像，支持中文描述。 |
| qwen-wanx-comic-gen | 使用通义万相（wan2.6-t2i）生成漫画/动漫风格图片。需配置 `DASHSCOPE_API_KEY`。 |
| stock-watcher | 自选股管理与近期表现汇总（数据来自同花顺 10jqka.com.cn），支持添加、删除、列表与汇总。 |
| web-scraper | 抓取网页并保存为 HTML 或 Markdown（含文本与图片），依赖少（requests、beautifulsoup4）。 |
| weibo-hot-search | 查询微博热搜、文娱热搜与热度排行。 |
| wuying-browser-use | 浏览器自动化：网页测试、表单填写、截图与数据提取。 |

使用与配置见各技能目录下的 `SKILL.md`。

## 仓库结构

```
agentbay-skills/
├── agentbay-aio-skills/       # 代码执行（SKILL.md + scripts）
├── agentbay-monitor-skills/   # 舆情监控与报告
├── amap-traffic/              # 高德路况与路线规划
├── boss-job-search/           # Boss 直聘职位搜索
├── china-stock-analysis/      # A 股分析与估值
├── douban-movie-review/       # 豆瓣电影影评
├── find-skills/               # 技能市场：搜索与安装
├── im-reminder/               # IM 定时提醒
├── moltbook-hot-posts/        # Moltbook 热帖
├── qwen-image/                # 通义万相图像生成
├── qwen-wanx-comic-gen/       # 万相漫画/动漫风格生成
├── stock-watcher/             # 自选股与行情汇总
├── web-scraper/               # 网页抓取为 HTML/Markdown
├── weibo-hot-search/          # 微博热搜
├── wuying-browser-use/        # 浏览器自动化
└── README.md
```

## 许可证

见仓库中的许可证文件。
