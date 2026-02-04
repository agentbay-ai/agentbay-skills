---
name: xiaohongshu-guide
description: 查询小红书攻略信息。当用户想要搜索小红书旅游攻略、美食攻略、购物攻略等各类攻略内容时使用此skill。
installation: |
  python -m pip install wuying-agentbay-sdk
---

# 小红书攻略查询

## 安装步骤

在使用此技能之前，请确保已安装必要的依赖包：

```bash
python -m pip install wuying-agentbay-sdk
```

## 使用场景

- 用户想搜索旅游攻略（如城市旅游、景点推荐）
- 用户想查找美食攻略（如餐厅推荐、美食探店）
- 用户想获取购物攻略（如好物推荐、品牌测评）
- 用户想了解生活攻略（如穿搭、化妆、健身等）

## 使用方法

```bash
python browser-use.py "<任务执行步骤>"
```

## 快速示例

### 示例1：搜索旅游攻略
```bash
python browser-use.py " \
1. 前往小红书网站 https://www.xiaohongshu.com/ \
2. 在搜索框中输入'成都旅游攻略' \
3. 点击搜索按钮进行搜索 \
4. 浏览搜索结果，提取前3条最热门的笔记信息 \
5. 记录每条笔记的标题、作者、点赞数和基本内容概述 \
6. 以markdown格式返回所有提取的攻略信息
"
```

### 示例2：搜索美食攻略
```bash
python browser-use.py " \
1. 访问小红书 https://www.xiaohongshu.com/ \
2. 搜索'上海网红餐厅' \
3. 筛选点赞数超过1000的笔记 \
4. 提取前8条美食推荐的详细信息 \
5. 以markdown格式整理返回
"
```

### 示例3：搜索穿搭攻略
```bash
python browser-use.py " \
1. 打开小红书网站 https://www.xiaohongshu.com/ \
2. 搜索'春季穿搭攻略' \
3. 按最新排序查看笔记 \
4. 提取前5条笔记的穿搭建议和搭配要点 \
5. 返回markdown格式的攻略总结
"
```

## 输出格式

```markdown
## 小红书攻略 - [搜索关键词]

### 热门笔记推荐

1. **笔记标题**
   - 作者: xxx
   - 点赞数: xxx
   - 收藏数: xxx
   - 内容概述: xxxxx

2. **笔记标题**
   - 作者: xxx
   - 点赞数: xxx
   - 收藏数: xxx
   - 内容概述: xxxxx

### 攻略总结
- 关键要点1
- 关键要点2
- 关键要点3

### 统计信息
- 总计: xx条笔记
- 平均点赞数: xxx
- 最高点赞数: xxx
```

## 注意事项

- 始终注明信息来源为小红书
- 不需要创建新的脚本，用skill目录下的browser-use.py
- 如果页面加载较慢，请耐心等待
- 任务执行需要1~2分钟，请耐心等待观察
- skill调用后，控制台会打印出asp流化链接（可视化的url），可告知用户查看
- 小红书内容会实时更新，以抓取时刻的数据为准
- 部分内容可能需要登录才能查看详细信息
