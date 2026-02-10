# AgentBay Skills

**English** | [中文](./README.zh-CN.md)

A collection of skills for [AgentBay](https://github.com/agentbay-ai), enabling agents to run code, use browser automation, monitor sentiment, and integrate with external services in a sandboxed environment.

## What's inside

| Skill | Description |
|-------|-------------|
| agentbay-aio-skills | Run or execute code (Python, JavaScript, R, Java) in an AgentBay sandbox. Triggered by "run this code", "execute this script", "帮我跑一下这段代码", etc. No need for the user to say "sandbox". |
| agent-browser-skills / boss-job-search | Search job postings on Boss直聘 (positions, company size filters). |
| agent-browser-skills / douban-movie-review | Query Douban movie reviews and ratings for a given film. |
| agent-browser-skills / moltbook-hot-posts | Query Moltbook (Agent community) hot posts and discussions. |
| agent-browser-skills / weibo-hot-search | Query Weibo hot search / trending topics. |
| agent-browser-skills / wuying-browser-use | Browser automation for testing, form filling, screenshots, and data extraction. |
| agentbay-monitor-skills | Sentiment/sentiment monitoring: crawl → sentiment analysis → generate report (Markdown/PDF). Triggered by "舆情分析", "舆情报告", etc. |
| find-skills | Discover, search and install agent skills from the marketplace. Use when the user wants to find a skill, install a capability, or look for sandbox-related skills. Triggered by "查找插件", "搜索技能", "install skill", "find a skill for X", etc. |

Usage and setup: see each skill's `SKILL.md` in its directory.

## Repository structure

```
agentbay-skills/
├── agentbay-aio-skills/       # Code execution (SKILL.md + scripts)
├── agent-browser-skills/      # Browser automation skills
│   ├── boss-job-search/
│   ├── douban-movie-review/
│   ├── moltbook-hot-posts/
│   ├── weibo-hot-search/
│   └── wuying-browser-use/
├── agentbay-monitor-skills/   # Sentiment monitoring & reporting
├── find-skills/               # Skill marketplace: search & install
└── README.md
```

## License

See repository license file.
