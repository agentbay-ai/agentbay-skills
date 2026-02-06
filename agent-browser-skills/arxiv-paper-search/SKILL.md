---
name: arxiv-paper-search
description: 查询arXiv论文信息。当用户想要搜索学术论文、查看arXiv最新研究、获取论文摘要和作者信息时使用此skill。
installation: |
  python -m pip install wuying-agentbay-sdk
---

# arXiv论文检索

## 安装步骤

在使用此技能之前,请确保已安装必要的依赖包：

```bash
python -m pip install wuying-agentbay-sdk
```

## 使用场景

- 用户想搜索特定主题的学术论文
- 用户想查看arXiv上的最新研究成果
- 用户需要获取论文的标题、作者、摘要等详细信息
- 用户想了解某个研究领域的前沿动态

## 使用方法

```bash
python scripts/browser-use.py "<任务执行步骤>"
```

## 快速示例

```bash
python scripts/browser-use.py " \
1. 前往arXiv官网 https://arxiv.org/ \
2. 等待页面完全加载 \
3. 在页面右上角的搜索框中输入'deep learning' \
4. 点击搜索按钮 \
5. 等待搜索结果页面加载完成 \
6. 点击前两篇文章的标题进入详情页 \
7. 在每篇文章的详情页中提取标题、作者列表、摘要内容 \
8. 以markdown格式返回所有提取的论文信息 \
"
```

## 输出格式

```markdown
## arXiv论文检索结果

### 检索关键词: deep learning

---

### 论文 1

**标题:** [论文标题]

**作者:** Author1, Author2, Author3

**提交时间:** YYYY-MM-DD

**论文链接:** https://arxiv.org/abs/XXXX.XXXXX

**摘要:**
[论文摘要内容的总结，简明扼要地描述研究目的、方法和主要发现]

---

### 论文 2

**标题:** [论文标题]

**作者:** Author1, Author2, Author3

**提交时间:** YYYY-MM-DD

**论文链接:** https://arxiv.org/abs/XXXX.XXXXX

**摘要:**
[论文摘要内容的总结，简明扼要地描述研究目的、方法和主要发现]

---

### 统计信息
- 检索结果总数: XX篇
- 已查看论文: 2篇
- 信息来源: arXiv.org
```

## 注意事项

- 始终注明信息来源为arXiv.org
- 不需要创建新的脚本，用skill目录下的browser-use.py
- arXiv页面可能需要时间加载，请耐心等待
- 摘要需要总结提炼，不要完整复制
- 论文信息以查询时刻为准
- 可以根据需要调整查看的论文数量
- 任务需要执行1~2分钟，不要杀进程，请耐心等待和观察任务，也不要重试
- skill调用后，控制台会打印出asp流化链接（可视化的url），可告知用户查看