# AgentBay Skills

**English** | [中文](./README.zh-CN.md)

A collection of skills for [AgentBay](https://github.com/agentbay-ai), enabling agents to run code, use browser automation, monitor sentiment, analyze stocks, generate images, and integrate with external services in a sandboxed environment.

## What's inside

| Skill | Description |
|-------|-------------|
| agentbay-aio-skills | Run or execute code (Python, JavaScript, R, Java) in an AgentBay sandbox. Triggered by "run this code", "execute this script", "帮我跑一下这段代码", etc. No need for the user to say "sandbox". |
| agentbay-monitor-skills | Sentiment monitoring: crawl → sentiment analysis → generate report (Markdown/PDF). Triggered by "舆情分析", "舆情报告", etc. |
| amap-traffic | Amap (高德) real-time traffic and optimal driving route planning. Requires `AMAP_KEY`. |
| boss-job-search | Search job postings on Boss直聘 (positions, company size filters). |
| china-stock-analysis | A-share value investing: stock screening, deep analysis, industry comparison, and valuation. Uses akshare for financial data. |
| douban-movie-review | Query Douban movie reviews and ratings for a given film. |
| find-skills | Discover, search and install agent skills from the marketplace. Triggered by "查找插件", "搜索技能", "install skill", "find a skill for X", etc. |
| im-reminder | IM scheduled reminders (one-time and recurring). Cron-based delivery to the original channel (Feishu, webchat). |
| moltbook-hot-posts | Query Moltbook (Agent community) hot posts and discussions. |
| qwen-image | Generate images via Qwen Image API (Alibaba Cloud DashScope). Text-to-image with Chinese prompts. |
| qwen-wanx-comic-gen | Generate comic/anime-style images with 通义万相 (wan2.6-t2i). Requires `DASHSCOPE_API_KEY`. |
| stock-watcher | Manage a stock watchlist and summarize performance (data from 10jqka.com.cn). Add, remove, list, summarize. |
| web-scraper | Scrape web pages and save as HTML or Markdown (text and images). Minimal deps: requests, beautifulsoup4. |
| weibo-hot-search | Query Weibo hot search / trending topics. |
| wuying-browser-use | Browser automation for testing, form filling, screenshots, and data extraction. |

Usage and setup: see each skill's `SKILL.md` in its directory.

## Repository structure

```
agentbay-skills/
├── agentbay-aio-skills/       # Code execution (SKILL.md + scripts)
├── agentbay-monitor-skills/   # Sentiment monitoring & reporting
├── amap-traffic/              # Amap traffic & route planning
├── boss-job-search/           # Boss直聘 job search
├── china-stock-analysis/      # A-share analysis & valuation
├── douban-movie-review/       # Douban movie reviews
├── find-skills/               # Skill marketplace: search & install
├── im-reminder/               # IM scheduled reminders
├── moltbook-hot-posts/        # Moltbook hot posts
├── qwen-image/                # Qwen Image API
├── qwen-wanx-comic-gen/       # Wanx comic/anime image gen
├── stock-watcher/             # Stock watchlist & performance
├── web-scraper/               # Web page to HTML/Markdown
├── weibo-hot-search/          # Weibo trending
├── wuying-browser-use/        # Browser automation
└── README.md
```

## License

See repository license file.
