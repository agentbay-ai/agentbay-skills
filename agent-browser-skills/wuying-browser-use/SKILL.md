---
name: wuying-browser-use
description: Automates browser interactions for web testing, form filling, screenshots, and data extraction. Use when the user needs to navigate websites, interact with web pages, or extract information.
allowed-tools: Bash(*)
---

# Wuying Browser Use

自动化浏览器操作，支持网页导航、表单填写、数据提取等任务。

## 使用方法

```bash
python browser-use.py "<任务执行步骤>"
```

## 快速示例

```bash
# 访问网站
python browser-use.py "<任务执行步骤>"

# 搜索信息
python browser-use.py "<任务执行步骤>"

# 提取数据
python browser-use.py "<任务执行步骤>"

# 填写表单
python browser-use.py "<任务执行步骤>"
```

## 功能特性

- ✅ 网页导航和点击
- ✅ 表单填写和提交
- ✅ 数据提取和抓取
- ✅ 网页截图
- ✅ 搜索和浏览
- ✅ 支持中英文指令

## 常用场景

### 电商信息收集
```bash
python browser-use.py "<任务执行步骤>" "访问京东搜索iPhone，提取前5个商品价格"
```

### 新闻监控
```bash
python browser-use.py "<任务执行步骤>" "打开新浪新闻，获取今日头条"
```

### 社交媒体
```bash
python browser-use.py "<任务执行步骤>" "访问微博热搜榜，提取前10个话题"
```

## 使用技巧

1. **指令要具体明确** - 说清楚要访问哪个网站，做什么操作
2. **一次一个任务** - 复杂流程拆分成多个命令
3. **描述性语言** - 详细描述要提取的内容或点击的元素

## 注意事项

- 每次命令独立运行，不保持会话状态
- 某些网站可能限制自动化访问
- 指令不明确可能导致非预期结果
- 每次执行需要1~2分钟，会不断产生中间结果，不要提前杀死进程，也不要重试
- skill调用后，控制台会打印出asp流化链接（可视化的url），可告知用户查看