# AgentBay Skills

[English](./README.md) | **中文**

[AgentBay](https://github.com/agentbay-ai) 的技能集合，支持在沙箱环境中运行代码、使用工具并与外部服务集成。

## 包含内容

| 技能 | 说明 |
|------|------|
| **agentbay-aio-skills** | 在 AgentBay 沙箱中运行代码（Python、JavaScript、R、Java）。由「run this code」「execute this script」「帮我跑一下这段代码」等表述触发，无需用户说「沙箱」。 |

## 快速开始

### 前置条件

- [wuying-agentbay-sdk](https://pypi.org/project/wuying-agentbay-sdk/)：`pip install wuying-agentbay-sdk`
- AgentBay API Key

### API Key 配置

在本地创建配置文件以便技能加载密钥：

- **macOS / Linux**：`~/.config/agentbay/api_key`
- **Windows**：`%APPDATA%\agentbay\api_key`

示例（macOS/Linux）：

```bash
mkdir -p ~/.config/agentbay
echo -n '你的_AgentBay_API_Key' > ~/.config/agentbay/api_key
```

### 通过脚本运行代码

```bash
cd agentbay-aio-skills
python scripts/run_code.py --code "print('Hello')" --language python
```

从文件运行：

```bash
python scripts/run_code.py --code-file ./examples/hello.py --language python
```

### 在代码中使用（SDK）

```python
from agentbay import AgentBay, CreateSessionParams

agent_bay = AgentBay(api_key="your_api_key")
result = agent_bay.create(CreateSessionParams(image_id="code_latest"))

code_result = result.session.code.run_code("print('Hello')", "python")
print(code_result.result)
result.session.delete()
```

完整技能说明、异步用法与结果处理见 [agentbay-aio-skills/SKILL.md](./agentbay-aio-skills/SKILL.md)。

## 仓库结构

```
agentbay-skills/
├── agentbay-aio-skills/    # 代码执行技能（SKILL.md + scripts）
├── dist/                   # 打包后的 .skill 文件
└── README.md
```

## 许可证

见仓库中的许可证文件。
