# AgentBay Skills

**English** | [中文](./README.zh-CN.md)

A collection of skills for [AgentBay](https://github.com/agentbay-ai), enabling agents to run code, use tools, and integrate with external services in a sandboxed environment.

## What's inside

| Skill | Description |
|-------|-------------|
| **agentbay-aio-skills** | Run or execute code (Python, JavaScript, R, Java) in an AgentBay sandbox. Triggered by phrases like "run this code", "execute this script", "帮我跑一下这段代码", etc. No need for the user to say "sandbox". |

## Quick start

### Prerequisites

- [wuying-agentbay-sdk](https://pypi.org/project/wuying-agentbay-sdk/): `pip install wuying-agentbay-sdk`
- An AgentBay API key

### API key configuration

Create a config file so the skill can load your key:

- **macOS / Linux**: `~/.config/agentbay/api_key`
- **Windows**: `%APPDATA%\agentbay\api_key`

Example (macOS/Linux):

```bash
mkdir -p ~/.config/agentbay
echo -n 'your_AgentBay_API_Key' > ~/.config/agentbay/api_key
```

### Run code via script

```bash
cd agentbay-aio-skills
python scripts/run_code.py --code "print('Hello')" --language python
```

With a file:

```bash
python scripts/run_code.py --code-file ./examples/hello.py --language python
```

### Use in code (SDK)

```python
from agentbay import AgentBay, CreateSessionParams

agent_bay = AgentBay(api_key="your_api_key")
result = agent_bay.create(CreateSessionParams(image_id="code_latest"))

code_result = result.session.code.run_code("print('Hello')", "python")
print(code_result.result)
result.session.delete()
```

See [agentbay-aio-skills/SKILL.md](./agentbay-aio-skills/SKILL.md) for full skill documentation, async usage, and result handling.

## Repository structure

```
agentbay-skills/
├── agentbay-aio-skills/    # Code execution skill (SKILL.md + scripts)
├── dist/                   # Built .skill packages
└── README.md
```

## License

See repository license file.
