---
name: pconline-3c-compare
description: 查询3C数码产品竞品对比信息。当用户想要对比手机、电脑、数码产品的参数配置、竞品分析时使用此skill。
installation: |
  python -m pip install wuying-agentbay-sdk
---

# 太平洋3C商品竞品对比查询

## 安装步骤

在使用此技能之前，请确保已安装必要的依赖包：

```bash
python -m pip install wuying-agentbay-sdk
```

## 使用场景

- 用户想对比某款手机与竞品的参数配置
- 用户想了解某款数码产品的竞品分析
- 用户想查看3C产品的详细规格对比

## 使用方法

```bash
python scripts/browser-use.py "<任务执行步骤>"
```

## 快速示例

```bash
python scripts/browser-use.py " \
1. 前往太平洋电脑网 https://www.pconline.com.cn/ \
2. 在搜索框中搜索 iPhone 17 \
3. 点击进入 iPhone 17 产品详情页面 \
4. 在左侧菜单点击竞品对比 \
5. 提取所有竞品分析对比资料 \
6. 以markdown格式返回对比结果 \
"
```

## 输出格式

```markdown
## 《产品名称》竞品对比分析

### 基本信息
- 产品名称: xxx
- 参考价格: xxx

### 竞品对比

| 参数 | 产品A | 产品B | 产品C |
|------|-------|-------|-------|
| 屏幕 | xxx | xxx | xxx |
| 处理器 | xxx | xxx | xxx |
| 内存 | xxx | xxx | xxx |
| 存储 | xxx | xxx | xxx |
| 电池 | xxx | xxx | xxx |
| 摄像头 | xxx | xxx | xxx |

### 对比总结
- 优势: xxx
- 劣势: xxx
```

## 注意事项

- 始终注明信息来源为太平洋电脑网
- 不需要创建新的脚本，用skill目录下的browser-use.py
- 如果产品页面加载较慢，请耐心等待
- skill调用后，控制台会打印出asp流化链接（可视化的url），可告知用户查看