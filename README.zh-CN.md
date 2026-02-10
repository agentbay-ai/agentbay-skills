# AgentBay Skills

[English](./README.md) | **中文**

[AgentBay](https://github.com/agentbay-ai) 的技能集合，支持在沙箱中运行代码、浏览器自动化、舆情监控并与外部服务集成。

## 包含内容

| 技能 | 说明 |
|------|------|
| agentbay-aio-skills | 在 AgentBay 沙箱中运行代码（Python、JavaScript、R、Java）。由「run this code」「帮我跑一下这段代码」等触发，无需说「沙箱」。 |
| agent-browser-skills / boss-job-search | 查询 Boss 直聘职位信息，支持职位、公司规模等筛选。 |
| agent-browser-skills / douban-movie-review | 查询豆瓣电影影评、评分与热门短评。 |
| agent-browser-skills / moltbook-hot-posts | 查询 Moltbook（Agent 社区）热帖与讨论。 |
| agent-browser-skills / weibo-hot-search | 查询微博热搜、文娱热搜与热度排行。 |
| agent-browser-skills / wuying-browser-use | 浏览器自动化：网页测试、表单填写、截图与数据提取。 |
| agentbay-monitor-skills | 舆情监控：爬取 → 情感分析 → 生成报告（Markdown/PDF）。由「舆情分析」「舆情报告」等触发。 |
| find-skills | 在技能市场中搜索、发现与安装 Agent 技能。当用户要查找插件、安装能力或寻找沙箱类技能时使用。触发词如「查找插件」「搜索技能」「install skill」「find a skill for X」等。 |

使用与配置见各技能目录下的 `SKILL.md`。

## 仓库结构

```
agentbay-skills/
├── agentbay-aio-skills/       # 代码执行（SKILL.md + scripts）
├── agent-browser-skills/      # 浏览器自动化类技能
│   ├── boss-job-search/
│   ├── douban-movie-review/
│   ├── moltbook-hot-posts/
│   ├── weibo-hot-search/
│   └── wuying-browser-use/
├── agentbay-monitor-skills/   # 舆情监控与报告
├── find-skills/               # 技能市场：搜索与安装
└── README.md
```

## 许可证

见仓库中的许可证文件。
